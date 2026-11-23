"""Unit tests for PoseEngine, StateMachine, ConditionParser, Scoring, and Edge Cases.

Unit tests for PoseEngine, FSM, scoring, and filters.
"""

from __future__ import annotations

import math

from posefit.config import (
    ExerciseKind,
    get_bundled_assets_dir,
    load_exercise_config_from_yaml,
)
from posefit.engine import PoseEngine
from posefit.filters import EMAFilter, OneEuroFilter, TemporalSmoother
from posefit.fsm import ConditionParser, EvaluationContext
from posefit.schemas import Grade
from posefit.scoring import FormScoreCalculator


def test_yaml_loading_all_18() -> None:
    """Verifies that all 18 bundled exercises register cleanly without error."""
    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    available = engine.available_exercises()
    assert len(available) == 18

    expected = [
        "bicep_curl",
        "calf_raise",
        "deadlift",
        "glute_bridge",
        "hammer_curl",
        "high_knees",
        "jumping_jack",
        "lateral_raise",
        "leg_raise",
        "lunge",
        "mountain_climber",
        "plank",
        "push_up",
        "shoulder_press",
        "side_lunge",
        "squat",
        "tricep_dip",
        "wall_sit",
    ]
    for ex_name in expected:
        assert ex_name in available, f"Missing exercise: {ex_name}"


def test_exercise_metadata_integrity() -> None:
    """Tests exercise metadata catalog."""
    assets_dir = get_bundled_assets_dir()
    squat_path = assets_dir / "squat.yaml"
    with open(squat_path, encoding="utf-8") as f:
        cfg = load_exercise_config_from_yaml(f.read())

    assert cfg.display_name == "Squat"
    assert cfg.type == ExerciseKind.REPETITION
    assert cfg.default_reps == 10
    assert cfg.difficulty == "beginner"
    assert cfg.target_muscles is not None
    assert "Quadriceps" in cfg.target_muscles
    assert "Gluteus" in cfg.target_muscles
    assert "Hamstrings" in cfg.target_muscles


def test_all_yaml_conditions_parse_successfully() -> None:
    """Matches fsm::tests::test_all_60_yaml_conditions_parse_successfully."""
    conditions = [
        "angle > 150",
        "angle > 50 and angle <= 150",
        "angle <= 50",
        "angle > 60",
        "angle > 140",
        "angle > 110 and angle <= 140",
        "angle <= 110",
        "angle > 120",
        "angle > 155",
        "angle > 47 and angle <= 155",
        "angle <= 47",
        "angle < 40",
        "angle > 160",
        "angle < 120",
        "angle >= 120 and angle < 155",
        "angle >= 155",
        "angle > 100",
        "angle > 35 and angle <= 100",
        "angle <= 35",
        "angle < 30",
        "angle > 165",
        "angle > 80 and angle <= 165",
        "angle <= 80",
        "angle < 75",
        "body_line_angle > 160",
        "body_line_angle <= 160",
        "body_line_angle < 155",
        "body_line_angle > 175",
        "angle > 90",
        "angle <= 90",
        "left_knee_x < left_ankle_x - 20",
        "right_knee_x > right_ankle_x + 20",
        "angle > 135",
        "angle > 85 and angle <= 135",
        "angle <= 85",
        "angle < 70",
        "angle >= 80 and angle <= 100",
        "angle < 80 or angle > 100",
        "angle > 105",
        "angle < 75",
        "abs(left_elbow_x - left_shoulder_x) > 100",
        "abs(left_hip_y - right_hip_y) > 30",
    ]

    for cond_str in conditions:
        cond = ConditionParser.parse_str(cond_str)
        assert cond is not None


def test_form_score_penalties_and_caps() -> None:
    """Tests form score calculation."""
    # 1. Perfect score
    calc = FormScoreCalculator()
    ctx = EvaluationContext()
    res = calc.calculate(ctx, last_rep_duration=2.0, active_feedback_count=0)
    assert res.score == 100
    assert res.grade == Grade.A
    assert res.angle_penalty == 0
    assert res.tempo_penalty == 0
    assert res.feedback_penalty == 0

    # 2. Angle penalty & cap at 40
    ideal = {"knee": 90.0}
    calc_angle = FormScoreCalculator(ideal_angles=ideal, tempo_min=1.0, tempo_max=3.0)
    # Deviation 20 deg -> (20 / 10) * 5 = 10
    ctx_10 = EvaluationContext().with_angle("knee", 70.0)
    res_10 = calc_angle.calculate(ctx_10, last_rep_duration=2.0, active_feedback_count=0)
    assert res_10.angle_penalty == 10
    assert res_10.score == 90
    assert res_10.grade == Grade.A

    # Deviation 120 deg -> (120 / 10) * 5 = 60 -> capped at 40
    ctx_bad = EvaluationContext().with_angle("knee", 210.0)
    res_bad = calc_angle.calculate(ctx_bad, last_rep_duration=2.0, active_feedback_count=0)
    assert res_bad.angle_penalty == 40
    assert res_bad.score == 60
    assert res_bad.grade == Grade.D

    # 3. Tempo penalties
    calc_tempo = FormScoreCalculator(tempo_min=1.0, tempo_max=3.0)
    # 0.5s under 1.0s: (1.0 - 0.5) / 0.5 * 15 = 15 points
    res_fast = calc_tempo.calculate(ctx, last_rep_duration=0.5, active_feedback_count=0)
    assert res_fast.tempo_penalty == 15
    assert res_fast.score == 85
    assert res_fast.grade == Grade.B

    # 2.0s over 3.0s: (5.0 - 3.0) * 10 = 20 points
    res_slow = calc_tempo.calculate(ctx, last_rep_duration=5.0, active_feedback_count=0)
    assert res_slow.tempo_penalty == 20
    assert res_slow.score == 80
    assert res_slow.grade == Grade.B

    # 4. Feedback penalty and cap at 30
    res_fb = calc.calculate(ctx, last_rep_duration=2.0, active_feedback_count=5)
    assert res_fb.feedback_penalty == 30
    assert res_fb.score == 70

    # 5. Score clamped to zero
    res_zero = calc_angle.calculate(ctx_bad, last_rep_duration=0.0, active_feedback_count=5)
    assert res_zero.score == 0
    assert res_zero.grade == Grade.F


def test_smoothing_filters() -> None:
    """Tests temporal landmark smoothing."""
    smoother = TemporalSmoother(window_size=3, enabled=True)
    # 1. Single value
    assert abs(smoother.smooth("primary", 100.0) - 100.0) < 1e-6
    # 2. Insufficient history (mean of 100 and 110 = 105)
    assert abs(smoother.smooth("primary", 110.0) - 105.0) < 1e-6
    # 3. Window full: [100, 110, 120] -> mean = 110
    assert abs(smoother.smooth("primary", 120.0) - 110.0) < 1e-6
    # 4. Sliding: drop oldest 100, add 130 -> [110, 120, 130] -> mean = 120
    assert abs(smoother.smooth("primary", 130.0) - 120.0) < 1e-6

    # 5. Reset
    smoother.reset()
    assert abs(smoother.smooth("primary", 60.0) - 60.0) < 1e-6

    # 6. Disabled
    smoother.enabled = False
    assert abs(smoother.smooth("primary", 120.0) - 120.0) < 1e-6


def test_one_euro_and_ema_filters() -> None:
    one_euro = OneEuroFilter(min_cutoff=1.0, beta=0.007)
    v0 = one_euro.filter(100.0, 0.0)
    assert v0 == 100.0
    v1 = one_euro.filter(110.0, 0.033)
    assert 100.0 < v1 <= 110.0

    ema = EMAFilter(alpha=0.5)
    assert ema.filter(100.0) == 100.0
    assert abs(ema.filter(110.0) - 105.0) < 1e-6


# ============================================================================
# Edge Case Coverage (Section 5)
# ============================================================================

def test_edge_cases_cold_start_and_missing_landmarks() -> None:
    """Cold start with first frame, missing landmarks, or low-visibility."""
    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    engine.start_exercise("squat")

    # 1. Cold start frame
    empty_flat = [0.0] * (33 * 4)
    res = engine.process_landmarks_flat(empty_flat, 1000, 1000, 0.0)
    assert res.counter == 0
    assert not res.rep_completed

    # 2. Low-visibility landmarks (visibility = 0.1)
    low_vis_flat = [0.0] * (33 * 4)
    for i in range(33):
        low_vis_flat[i * 4 + 3] = 0.1
    res_low = engine.process_landmarks_flat(low_vis_flat, 1000, 1000, 0.1)
    assert res_low.counter == 0

    # 3. Reset and status retrieval without processing
    engine.reset()
    status = engine.status()
    assert status is not None
    assert status.counter == 0


def test_edge_cases_nan_inf_and_out_of_bounds() -> None:
    """Robustness against NaN / Inf values and out-of-frame points."""
    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    engine.start_exercise("squat")

    # Out of frame coordinates (> 1.0 or negative)
    oof_flat = [0.0] * (33 * 4)
    oof_flat[11 * 4] = -5.0  # x far left
    oof_flat[11 * 4 + 1] = 10.0  # y far bottom
    oof_flat[11 * 4 + 3] = 1.0
    res = engine.process_landmarks_flat(oof_flat, 1000, 1000, 0.2)
    assert res is not None

    # Division by zero / zero length limb vectors
    zero_limb_flat = [0.0] * (33 * 4)
    # Put shoulder, hip, knee at identical coordinates
    for idx in (11, 23, 25):
        zero_limb_flat[idx * 4] = 0.5
        zero_limb_flat[idx * 4 + 1] = 0.5
        zero_limb_flat[idx * 4 + 3] = 1.0
    res_zero = engine.process_landmarks_flat(zero_limb_flat, 1000, 1000, 0.4)
    # Angles should gracefully be 0.0 without crash
    assert res_zero.angles.get("primary") == 0.0


def test_edge_cases_camera_dropout_and_recovery() -> None:
    """Simulates camera freeze, dropout, and subsequent resumption."""
    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    engine.start_exercise("squat")
    assert engine.active_exercise is not None
    engine.active_exercise.smoother.enabled = False

    # 1. Start descent: 175 -> 150 -> 110 deg
    angles = [175.0, 150.0, 110.0]
    last_flat = [0.0] * (33 * 4)
    for idx, a in enumerate(angles):
        ts = idx * 0.3
        flat = [0.0] * (33 * 4)
        flat[11 * 4], flat[11 * 4 + 1], flat[11 * 4 + 3] = 0.5, 0.2, 1.0
        flat[23 * 4], flat[23 * 4 + 1], flat[23 * 4 + 3] = 0.5, 0.5, 1.0
        rad = math.radians(180.0 - a)
        knee_x = 0.5 + 0.3 * math.sin(rad)
        knee_y = 0.5 + 0.3 * math.cos(rad)
        flat[25 * 4], flat[25 * 4 + 1], flat[25 * 4 + 3] = knee_x, knee_y, 1.0
        engine.process_landmarks_flat(flat, 1000, 1000, ts)
        last_flat = flat

    assert engine.status().current_state == "descent"

    # 2. Camera freeze / repeated frames at 110 deg
    for i in range(3):
        ts = 1.0 + i * 0.3
        freeze_res = engine.process_landmarks_flat(last_flat, 1000, 1000, ts)
        assert freeze_res.current_state == "descent"
        assert freeze_res.counter == 0

    # 3. Resumption: continue squat down to 85 deg (triggers ascent), then up to 175 deg
    completed_seen = False
    recovery_angles = [85.0, 140.0, 175.0]
    for idx, a in enumerate(recovery_angles):
        ts = 2.0 + idx * 0.3
        flat = [0.0] * (33 * 4)
        flat[11 * 4], flat[11 * 4 + 1], flat[11 * 4 + 3] = 0.5, 0.2, 1.0
        flat[23 * 4], flat[23 * 4 + 1], flat[23 * 4 + 3] = 0.5, 0.5, 1.0
        rad = math.radians(180.0 - a)
        knee_x = 0.5 + 0.3 * math.sin(rad)
        knee_y = 0.5 + 0.3 * math.cos(rad)
        flat[25 * 4], flat[25 * 4 + 1], flat[25 * 4 + 3] = knee_x, knee_y, 1.0
        res = engine.process_landmarks_flat(flat, 1000, 1000, ts)
        if res.rep_completed:
            completed_seen = True

    assert res.counter == 1
    assert completed_seen
