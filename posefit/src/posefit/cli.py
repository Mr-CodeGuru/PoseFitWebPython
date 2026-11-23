"""Command-line interface for PoseFit: serve, bench, and replay."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from posefit.engine import PoseEngine


def cmd_serve(args: argparse.Namespace) -> None:
    """Runs the FastAPI server via uvicorn."""
    import uvicorn

    uvicorn.run(
        "posefit.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


def cmd_bench(args: argparse.Namespace) -> None:
    """Runs the benchmark suite."""
    from posefit.bench.bench_engine import run_benchmark

    run_benchmark(num_frames=args.frames, exercise=args.exercise)


def cmd_replay(args: argparse.Namespace) -> None:
    """Replays a recorded golden landmark JSON file."""
    import json

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: Fixture file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    frames = data if isinstance(data, list) else data.get("frames", [])
    if not frames:
        print("Error: No frames found in input file.", file=sys.stderr)
        sys.exit(1)

    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    engine.start_exercise(args.exercise)

    print(f"Replaying {len(frames)} frames for exercise '{args.exercise}'...")
    start_t = time.perf_counter()

    for f_idx, frame in enumerate(frames):
        if "flat_landmarks" in frame:
            flat = frame["flat_landmarks"]
        elif "landmarks" in frame:
            flat = []
            for lm in frame["landmarks"]:
                flat.extend([
                    lm.get("x", 0.0),
                    lm.get("y", 0.0),
                    lm.get("z", 0.0),
                    lm.get("visibility", 1.0),
                ])
        else:
            continue

        w = frame.get("width", 1280)
        h = frame.get("height", 720)
        ts = frame.get("timestamp_sec", f_idx * 0.033)

        res = engine.process_landmarks_flat(flat, w, h, ts)
        if res.rep_completed:
            print(
                f"Frame {f_idx}: Rep completed! "
                f"Total count: {res.counter}, Score: {res.form_score} ({res.form_grade})"
            )

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    summary = engine.stop_exercise()

    print("\n--- Replay Complete ---")
    print(f"Total Reps: {summary.total_reps}")
    print(f"Average Form Score: {summary.avg_form_score} (Grade {summary.final_grade})")
    print(f"Replay Time: {elapsed_ms:.2f} ms ({len(frames) / (elapsed_ms / 1000.0):.1f} FPS)")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="posefit",
        description="PoseFit pure-Python kinematics engine and server CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: serve
    p_serve = subparsers.add_parser("serve", help="Start the FastAPI WebSocket server")
    p_serve.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind (default: 127.0.0.1)",
    )
    p_serve.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload on code change")

    # Subcommand: bench
    p_bench = subparsers.add_parser("bench", help="Run latency and memory benchmark")
    p_bench.add_argument(
        "--frames",
        type=int,
        default=1000,
        help="Number of synthetic frames (default: 1000)",
    )
    p_bench.add_argument(
        "--exercise",
        default="squat",
        help="Exercise name to benchmark (default: squat)",
    )

    # Subcommand: replay
    p_replay = subparsers.add_parser(
        "replay",
        help="Replay a landmark sequence file through the engine",
    )
    p_replay.add_argument("file", help="Path to JSON file containing landmark sequence")
    p_replay.add_argument("--exercise", default="squat", help="Exercise to run (default: squat)")

    args = parser.parse_args()
    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "bench":
        cmd_bench(args)
    elif args.command == "replay":
        cmd_replay(args)


if __name__ == "__main__":
    main()
