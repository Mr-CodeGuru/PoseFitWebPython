"""Golden Reference Parity Test Suite.

Validates against golden reference landmark fixture sequences:
- Angles match within 1e-4 degrees
- Rep counts and state transitions are identical frame-for-frame
- Feedback strings, severities, and form scores match identically
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from posefit.engine import PoseEngine


@pytest.fixture(scope="module")
def golden_fixtures_data() -> dict:
    """Loads golden fixtures reference JSON."""
    fixtures_path = Path(__file__).resolve().parent / "fixtures" / "golden_fixtures.json"
    assert fixtures_path.exists(), f"Fixtures file missing at {fixtures_path}"
    with open(fixtures_path, encoding="utf-8") as f:
        return json.load(f)


def test_golden_parity_all_cases(golden_fixtures_data: dict) -> None:
    """Asserts frame-by-frame parity against golden fixture sequences."""
    cases = golden_fixtures_data.get("cases", [])
    assert len(cases) >= 5, "Expected at least 5 golden test fixture cases"

    for case in cases:
        exercise_name = case["exercise_name"]
        smoothing_enabled = case.get("smoothing_enabled", True)
        description = case.get("description", "")
        frames = case["frames"]

        engine = PoseEngine()
        engine.register_all_bundled_exercises()
        engine.start_exercise(exercise_name)

        # Set smoothing mode on active exercise
        assert engine.active_exercise is not None
        if hasattr(engine.active_exercise, "smoother"):
            engine.active_exercise.smoother.enabled = smoothing_enabled

        # Set target duration if overridden in the test case fixture
        if frames and frames[0]["expected_result"].get("target_duration") is not None:
            if hasattr(engine.active_exercise, "target_duration"):
                exp_dur = frames[0]["expected_result"]["target_duration"]
                engine.active_exercise.target_duration = exp_dur

        for frame in frames:
            f_idx = frame["frame_idx"]
            ts = frame["timestamp_sec"]
            width = frame["width"]
            height = frame["height"]
            flat_landmarks = frame["flat_landmarks"]
            expected = frame["expected_result"]

            actual = engine.process_landmarks_flat(flat_landmarks, width, height, ts)

            # 1. Assert Rep Count Parity
            assert actual.counter == expected["counter"], (
                f"[{description}] Frame {f_idx}: Rep counter mismatch. "
                f"Expected {expected['counter']}, got {actual.counter}"
            )

            # 2. Assert Bilateral Counters if present
            assert actual.counter_left == expected.get("counter_left", 0)
            assert actual.counter_right == expected.get("counter_right", 0)

            # 3. Assert State Machine Transition Parity
            assert actual.current_state == expected["current_state"], (
                f"[{description}] Frame {f_idx}: current_state mismatch. "
                f"Expected {expected['current_state']}, got {actual.current_state}"
            )
            assert actual.prev_state == expected["prev_state"], (
                f"[{description}] Frame {f_idx}: prev_state mismatch. "
                f"Expected {expected['prev_state']}, got {actual.prev_state}"
            )
            assert actual.rep_completed == expected.get("rep_completed", False), (
                f"[{description}] Frame {f_idx}: rep_completed flag mismatch."
            )

            # 4. Assert Angles Parity (tolerance <= 1e-4 degrees)
            expected_angles = expected.get("angles", {})
            for angle_name, exp_val in expected_angles.items():
                assert angle_name in actual.angles, (
                    f"[{description}] Frame {f_idx}: Missing angle '{angle_name}' in output"
                )
                act_val = actual.angles[angle_name]
                assert abs(act_val - exp_val) < 1e-4, (
                    f"[{description}] Frame {f_idx}: Angle '{angle_name}' deviation exceeds 1e-4. "
                    f"Expected {exp_val:.6f}, got {act_val:.6f}"
                )

            # 5. Assert Form Scores and Grades
            assert actual.form_score == expected["form_score"], (
                f"[{description}] Frame {f_idx}: form_score mismatch. "
                f"Expected {expected['form_score']}, got {actual.form_score}"
            )
            assert actual.avg_form_score == expected.get("avg_form_score", 100)
            assert actual.form_grade.value == expected["form_grade"]

            # 6. Assert Feedback Alert Messages & Severities
            expected_alerts = expected.get("feedback_alerts", [])
            assert len(actual.feedback_alerts) == len(expected_alerts), (
                f"[{description}] Frame {f_idx}: Alert count mismatch. "
                f"Expected {len(expected_alerts)}, got {len(actual.feedback_alerts)}"
            )
            for exp_a, act_a in zip(expected_alerts, actual.feedback_alerts, strict=False):
                assert act_a.name == exp_a["name"]
                assert act_a.message == exp_a["message"]
                assert act_a.severity.value == exp_a["severity"]
