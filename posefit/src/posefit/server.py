"""FastAPI transport layer providing WebSocket streaming, REST catalog, and SPA static hosting.

Fully offline, local-first. Isolates PoseEngine instances per WebSocket connection.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from posefit.engine import PoseEngine

# Optional performance serializes
try:
    import orjson

    def json_dumps(obj: Any) -> str:
        return orjson.dumps(obj).decode("utf-8")

    def json_loads(data: str | bytes) -> Any:
        return orjson.loads(data)

except ImportError:
    import json

    def json_dumps(obj: Any) -> str:
        return json.dumps(obj)

    def json_loads(data: str | bytes) -> Any:
        return json.loads(data)

try:
    import msgpack  # type: ignore
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False

logger = logging.getLogger("posefit.server")

# Global master engine for exercise catalog inspection
master_engine = PoseEngine()

MAX_TEXT_MESSAGE_BYTES: int = 65536  # 64 KB for landmark JSON
MAX_BINARY_FRAME_BYTES: int = 5 * 1024 * 1024  # 5 MB for Mode B image frame


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Pre-registers all bundled exercise YAML configurations on startup."""
    try:
        master_engine.register_all_bundled_exercises()
        logger.info(
            "Loaded %d bundled exercises successfully",
            len(master_engine.available_exercises()),
        )
    except Exception as exc:
        logger.warning("Failed to load bundled exercises at startup: %s", exc)
    yield


app = FastAPI(
    title="PoseFit Kinematics Server",
    description="Local-first AI fitness kinematics engine and WebSocket transport",
    version="0.1.0",
    lifespan=lifespan,
)

# Strict CORS allowed origins: local Vite development server
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Liveness probe confirming server readiness and local-only mode."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": "local",
        "has_orjson": "orjson" in globals(),
        "has_msgpack": HAS_MSGPACK,
    }


@app.get("/api/exercises")
async def list_exercises() -> list[dict[str, Any]]:
    """Returns catalog of all registered exercise profiles."""
    if not master_engine.available_exercises():
        master_engine.register_all_bundled_exercises()

    catalog: list[dict[str, Any]] = []
    for name in master_engine.available_exercises():
        cfg = master_engine.configs[name]
        catalog.append({
            "id": cfg.name,
            "name": cfg.display_name or cfg.name,
            "type": cfg.type.value,
            "bilateral": cfg.bilateral,
            "target_muscles": cfg.target_muscles or [],
            "difficulty": cfg.difficulty or "beginner",
            "default_reps": cfg.default_reps or 10,
            "description": cfg.description or "",
        })
    return catalog


@app.websocket("/ws/pose")
async def websocket_pose_session(
    websocket: WebSocket,
    exercise: str = Query(default="squat"),
    use_msgpack: bool = Query(default=False),
) -> None:
    """Per-connection isolated kinematics session over WebSocket."""
    await websocket.accept()

    # Create isolated PoseEngine instance for this user session
    session_engine = PoseEngine()
    try:
        session_engine.register_all_bundled_exercises()
        session_engine.start_exercise(exercise)
    except Exception as exc:
        logger.error("Failed to initialize session for exercise '%s': %s", exercise, exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        return

    # Frame skipping queue for Mode B backpressure (keep only the newest frame)
    frame_queue: asyncio.Queue[bytes | str] = asyncio.Queue(maxsize=2)

    async def sender_worker() -> None:
        """Worker task draining the queue, evaluating the engine, and replying to client."""
        while True:
            try:
                raw_item = await frame_queue.get()
            except asyncio.CancelledError:
                break

            try:
                result_payload: dict[str, Any] | None = None

                # 1. Binary message: flat Float32Array or Mode B image bytes
                if isinstance(raw_item, bytes):
                    if len(raw_item) == 33 * 4 * 4:  # 33 landmarks * 4 floats * 4 bytes = 528 bytes
                        import numpy as np
                        flat_arr = np.frombuffer(raw_item, dtype=np.float32)
                        now_ts = asyncio.get_event_loop().time()
                        res = session_engine.process_landmarks_flat(flat_arr, 1280, 720, now_ts)
                        result_payload = res.model_dump()
                    elif session_engine.estimator is not None:
                        # Mode B image frame
                        now_ts = asyncio.get_event_loop().time()
                        res = session_engine.process_image_bytes(raw_item, 1280, 720, now_ts)
                        result_payload = res.model_dump()

                # 2. Text message: JSON command or flat landmark payload
                elif isinstance(raw_item, str):
                    parsed = json_loads(raw_item)
                    action = parsed.get("action", "frame")

                    if action == "start":
                        target_ex = parsed.get("exercise", exercise)
                        session_engine.start_exercise(target_ex)
                        result_payload = {"status": "started", "exercise": target_ex}

                    elif action == "stop":
                        summary = session_engine.stop_exercise()
                        result_payload = {"status": "stopped", "summary": summary.model_dump()}

                    elif action == "reset":
                        session_engine.reset()
                        result_payload = {"status": "reset"}

                    elif action == "frame":
                        flat = parsed.get("flat_landmarks")
                        if flat and len(flat) >= 33 * 4:
                            w = int(parsed.get("width", 1280))
                            h = int(parsed.get("height", 720))
                            ts = float(parsed.get("timestamp_sec", asyncio.get_event_loop().time()))
                            res = session_engine.process_landmarks_flat(flat, w, h, ts)
                            result_payload = res.model_dump()

                if result_payload is not None:
                    if use_msgpack and HAS_MSGPACK:
                        packed = msgpack.packb(result_payload)
                        await websocket.send_bytes(packed)
                    else:
                        text_resp = json_dumps(result_payload)
                        await websocket.send_text(text_resp)

            except Exception as e:
                logger.warning("Error processing frame: %s", e)
                err_resp = json_dumps({"error": str(e)})
                await websocket.send_text(err_resp)
            finally:
                frame_queue.task_done()

    worker_task = asyncio.create_task(sender_worker())

    try:
        while True:
            # Receive frame with message-size validation
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            data_bytes = message.get("bytes")
            data_text = message.get("text")

            item_to_enqueue: bytes | str | None = None

            if data_bytes is not None:
                if len(data_bytes) > MAX_BINARY_FRAME_BYTES:
                    logger.warning("Binary message exceeds limit (%d bytes)", len(data_bytes))
                    continue
                item_to_enqueue = data_bytes
            elif data_text is not None:
                if len(data_text) > MAX_TEXT_MESSAGE_BYTES:
                    logger.warning("Text message exceeds limit (%d bytes)", len(data_text))
                    continue
                item_to_enqueue = data_text

            if item_to_enqueue is not None:
                # Backpressure: if queue is full, drop oldest stale frame
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                        frame_queue.task_done()
                    except (asyncio.QueueEmpty, ValueError):
                        pass
                await frame_queue.put(item_to_enqueue)

    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected normally")
    except Exception as exc:
        logger.error("WebSocket session exception: %s", exc)
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


# Static frontend hosting with Single-Page Application (SPA) fallback
DIST_DIRS = [
    Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist",
    Path(__file__).resolve().parent.parent.parent.parent / "dist",
    Path(__file__).resolve().parent / "static",
]

static_dir: Path | None = None
for candidate in DIST_DIRS:
    if candidate.exists() and candidate.is_dir():
        static_dir = candidate
        break

if static_dir and (static_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        """Serves built static assets or falls back to index.html for client-side routing."""
        assert static_dir is not None
        target = static_dir / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(static_dir / "index.html")
