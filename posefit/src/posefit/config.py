"""PoseFit System Configuration, Constants, and Exercise Definitions.

System configuration, constants, and exercise schema models.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from posefit.schemas import Severity

# ============================================================================
# 1. Landmark Constants
# ============================================================================

NOSE: int = 0  # landmarks.rs:34
LEFT_SHOULDER: int = 11  # landmarks.rs:35
RIGHT_SHOULDER: int = 12  # landmarks.rs:36
LEFT_ELBOW: int = 13  # landmarks.rs:37
RIGHT_ELBOW: int = 14  # landmarks.rs:38
LEFT_WRIST: int = 15  # landmarks.rs:39
RIGHT_WRIST: int = 16  # landmarks.rs:40
LEFT_HIP: int = 23  # landmarks.rs:41
RIGHT_HIP: int = 24  # landmarks.rs:42
LEFT_KNEE: int = 25  # landmarks.rs:43
RIGHT_KNEE: int = 26  # landmarks.rs:44
LEFT_ANKLE: int = 27  # landmarks.rs:45
RIGHT_ANKLE: int = 28  # landmarks.rs:46

# Complete mapping of supported MediaPipe landmark names to integer indices
LANDMARK_NAME_TO_INDEX: dict[str, int] = {
    "nose": NOSE,
    "left_shoulder": LEFT_SHOULDER,
    "right_shoulder": RIGHT_SHOULDER,
    "left_elbow": LEFT_ELBOW,
    "right_elbow": RIGHT_ELBOW,
    "left_wrist": LEFT_WRIST,
    "right_wrist": RIGHT_WRIST,
    "left_hip": LEFT_HIP,
    "right_hip": RIGHT_HIP,
    "left_knee": LEFT_KNEE,
    "right_knee": RIGHT_KNEE,
    "left_ankle": LEFT_ANKLE,
    "right_ankle": RIGHT_ANKLE,
}

INDEX_TO_LANDMARK_NAME: dict[int, str] = {v: k for k, v in LANDMARK_NAME_TO_INDEX.items()}

# ============================================================================
# 2. Kinematic & Mathematical Tolerances
# ============================================================================

FLOAT_EQUALITY_EPSILON: float = 1e-5   # for == and != operator evaluation
ANGLE_PARITY_EPSILON: float = 1e-4   # for angle precision verification

# ============================================================================
# 3. Scoring & Penalty Constants
# ============================================================================

BASE_FORM_SCORE: int = 100  # scoring.rs:84
MAX_ANGLE_PENALTY: int = 40  # scoring.rs:88
MAX_TEMPO_PENALTY: int = 30  # scoring.rs:93
MAX_FEEDBACK_PENALTY: int = 30  # scoring.rs:98
FEEDBACK_PENALTY_PER_ALERT: int = 10  # scoring.rs:97

ANGLE_PENALTY_DIVISOR: float = 10.0  # scoring.rs:125
ANGLE_PENALTY_MULTIPLIER: float = 5.0  # scoring.rs:125

TEMPO_FAST_STEP_SEC: float = 0.5  # scoring.rs:144
TEMPO_FAST_PENALTY_PER_STEP: float = 15.0  # scoring.rs:144
TEMPO_SLOW_PENALTY_PER_SEC: float = 10.0  # scoring.rs:147

DEFAULT_TEMPO_MIN: float = 1.0  # definitions/schema.rs:55
DEFAULT_TEMPO_MAX: float = 3.0  # definitions/schema.rs:58

# ============================================================================
# 4. Temporal Smoothing Defaults
# ============================================================================

DEFAULT_SMOOTHING_ENABLED: bool = True  # schema.rs:70
DEFAULT_SMOOTHING_WINDOW: int = 3  # schema.rs:73

# ============================================================================
# 5. Repetition & Duration Defaults
# ============================================================================

DEFAULT_MIN_REP_DURATION: float = 0.8  # standard.rs:98, bilateral.rs:109
DEFAULT_TARGET_DURATION: float = 30.0  # duration.rs:95
DEFAULT_HOLD_STATE: str = "hold"  # duration.rs:94


# ============================================================================
# 6. Pydantic v2 Exercise Configuration Models (matching schema.rs)
# ============================================================================

class ExerciseKind(StrEnum):
    """Categorical classification of exercise tracking mode."""

    REPETITION = "repetition"
    DURATION = "duration"


class AngleConfig(BaseModel):
    """Configuration for a specific tracked joint angle triplet."""

    model_config = ConfigDict(extra="ignore")

    points: list[str]
    description: str | None = None


class StateConfig(BaseModel):
    """FSM state activation condition and user-facing description."""

    model_config = ConfigDict(extra="ignore")

    condition: str
    description: str | None = None


class CounterConfig(BaseModel):
    """Repetition counter triggering and transition prerequisite."""

    model_config = ConfigDict(extra="ignore")

    trigger_state: str
    from_state: str | None = None


class FeedbackConfig(BaseModel):
    """Real-time biomechanical feedback heuristic rule."""

    model_config = ConfigDict(extra="ignore")

    condition: str
    message: str = "Form warning"
    severity: Severity = Severity.WARNING


class TempoConfig(BaseModel):
    """Ideal repetition cadence bounds (seconds)."""

    model_config = ConfigDict(extra="ignore")

    min: float = DEFAULT_TEMPO_MIN
    max: float = DEFAULT_TEMPO_MAX


class SmoothingConfig(BaseModel):
    """Angle smoothing filter settings."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = DEFAULT_SMOOTHING_ENABLED
    window: int = DEFAULT_SMOOTHING_WINDOW


class CalibrationConfig(BaseModel):
    """Optional baseline framing calibration settings."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = False
    reps: int = 0


class ExerciseConfig(BaseModel):
    """Complete declarative exercise configuration model."""

    model_config = ConfigDict(extra="ignore")

    name: str
    display_name: str | None = None
    type: ExerciseKind = ExerciseKind.REPETITION
    bilateral: bool = False
    sides: list[str] = Field(default_factory=list)
    target_duration: float | None = None
    hold_state: str | None = None
    angles: dict[str, AngleConfig] = Field(default_factory=dict)
    state_order: list[str] = Field(default_factory=list)
    states: dict[str, StateConfig] = Field(default_factory=dict)
    counter: CounterConfig | None = None
    min_rep_duration: float | None = None
    feedback: dict[str, FeedbackConfig] = Field(default_factory=dict)
    tempo: TempoConfig | None = None
    ideal_angles: dict[str, float] | None = None
    smoothing: SmoothingConfig | None = None
    calibration: CalibrationConfig | None = None
    visualization: Any = None
    target_muscles: list[str] | None = None
    equipment: str | None = None
    difficulty: str | None = None
    default_reps: int | None = None
    default_sets: int | None = None
    rest_time: str | None = None
    benefits: list[str] | None = None
    description: str | None = None


def load_exercise_config_from_yaml(yaml_str: str) -> ExerciseConfig:
    """Parses and validates a YAML exercise configuration string."""
    data = yaml.safe_load(yaml_str)
    config = ExerciseConfig.model_validate(data)
    validate_exercise_semantics(config)
    return config


def validate_exercise_semantics(config: ExerciseConfig) -> None:
    """Validates exercise structural and semantic integrity."""
    # 1. Validate angle points map to known MediaPipe landmarks
    for angle_name, angle_def in config.angles.items():
        if len(angle_def.points) != 3:
            raise ValueError(
                f"Angle '{angle_name}' must define exactly 3 points, got {len(angle_def.points)}"
            )
        for pt in angle_def.points:
            if pt not in LANDMARK_NAME_TO_INDEX:
                raise ValueError(f"Angle '{angle_name}' references unknown landmark '{pt}'")

    # 2. Validate state_order references existing states
    for state_name in config.state_order:
        if state_name not in config.states:
            raise ValueError(f"state_order references undefined state '{state_name}'")

    # 3. Validate counter configuration
    if config.counter is not None:
        if config.counter.trigger_state not in config.states:
            raise ValueError(
                f"counter trigger_state '{config.counter.trigger_state}' not found in states"
            )
        if config.counter.from_state and config.counter.from_state not in config.states:
            raise ValueError(
                f"counter from_state '{config.counter.from_state}' not found in states"
            )


def get_bundled_assets_dir() -> Path:
    """Returns path to bundled exercise assets in the local package."""
    return Path(__file__).resolve().parent / "assets" / "exercises"
