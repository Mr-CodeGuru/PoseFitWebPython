"""Tests for FastAPI HTTP routes, WebSocket kinematics streaming, and session isolation.

Validates Section 6 server specification.
"""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from posefit.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["mode"] == "local"


def test_list_exercises_endpoint(client: TestClient) -> None:
    response = client.get("/api/exercises")
    assert response.status_code == 200
    catalog = response.json()
    assert isinstance(catalog, list)
    assert len(catalog) == 18
    names = [ex["id"] for ex in catalog]
    assert "squat" in names
    assert "push_up" in names
    assert "plank" in names
    assert "hammer_curl" in names


def test_websocket_pose_session_lifecycle(client: TestClient) -> None:
    """Tests complete WebSocket session: connecting, sending frames, rep counting, and stop."""
    with client.websocket_connect("/ws/pose?exercise=squat") as ws:
        # 1. Send first standing frame
        flat = [0.0] * (33 * 4)
        flat[11 * 4], flat[11 * 4 + 1], flat[11 * 4 + 3] = 0.5, 0.2, 1.0  # shoulder
        flat[23 * 4], flat[23 * 4 + 1], flat[23 * 4 + 3] = 0.5, 0.5, 1.0  # hip
        flat[25 * 4], flat[25 * 4 + 1], flat[25 * 4 + 3] = 0.5, 0.8, 1.0  # knee (straight ~180)

        ws.send_text(json.dumps({
            "action": "frame",
            "flat_landmarks": flat,
            "width": 1000,
            "height": 1000,
            "timestamp_sec": 0.0,
        }))

        resp_text = ws.receive_text()
        resp_data = json.loads(resp_text)
        assert resp_data["exercise_name"] == "squat"
        assert resp_data["counter"] == 0
        assert resp_data["current_state"] == "start"

        # 2. Reset exercise
        ws.send_text(json.dumps({"action": "reset"}))
        resp_reset = json.loads(ws.receive_text())
        assert resp_reset["status"] == "reset"

        # 3. Stop exercise and verify WorkoutSummary
        ws.send_text(json.dumps({"action": "stop"}))
        resp_stop = json.loads(ws.receive_text())
        assert resp_stop["status"] == "stopped"
        assert "summary" in resp_stop
        summary = resp_stop["summary"]
        assert summary["exercise_name"] == "squat"
        assert "total_reps" in summary
        assert "final_grade" in summary


def test_websocket_session_isolation(client: TestClient) -> None:
    """Verifies that multiple concurrent WebSocket sessions maintain independent state."""
    with client.websocket_connect("/ws/pose?exercise=squat") as ws1:
        with client.websocket_connect("/ws/pose?exercise=push_up") as ws2:
            # Session 1 sends frame
            flat = [0.0] * (33 * 4)
            ws1.send_text(json.dumps({
                "action": "frame",
                "flat_landmarks": flat,
                "timestamp_sec": 0.0,
            }))
            resp1 = json.loads(ws1.receive_text())
            assert resp1["exercise_name"] == "squat"

            # Session 2 sends frame
            ws2.send_text(json.dumps({
                "action": "frame",
                "flat_landmarks": flat,
                "timestamp_sec": 0.0,
            }))
            resp2 = json.loads(ws2.receive_text())
            assert resp2["exercise_name"] == "push_up"
