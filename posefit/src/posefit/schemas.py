"""Pydantic v2 and typed schemas for PoseFit requests, responses, and engine state."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    """Feedback alert severity category."""

    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class Grade(StrEnum):
    """Form letter grade derived from numerical score (0-100)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

    @classmethod
    def from_score(cls, score: int) -> Grade:
        """Determines grade tier from 0-100 numerical score."""
        if score >= 90:
            return cls.A
        if score >= 80:
            return cls.B
        if score >= 70:
            return cls.C
        if score >= 60:
            return cls.D
        return cls.F


class FeedbackAlert(BaseModel):
    """Individual biomechanical warning or form suggestion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    message: str
    severity: Severity = Severity.WARNING


class FormScoreBreakdown(BaseModel):
    """Detailed penalty itemization for form scoring."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: int
    grade: Grade
    angle_penalty: int
    tempo_penalty: int
    feedback_penalty: int


class Landmark(BaseModel):
    """3D human pose landmark coordinate and detection confidences."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0
    presence: float = 1.0

    def to_pixel_coords(self, width: int, height: int) -> tuple[int, int]:
        """Convert normalized [0.0, 1.0] coordinates to discrete pixel integers."""
        return int(self.x * width), int(self.y * height)


class ExerciseResult(BaseModel):
    """Complete per-frame evaluation response returned to the frontend."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    exercise_name: str
    counter: int = 0
    counter_left: int = 0
    counter_right: int = 0
    current_state: str | None = None
    prev_state: str | None = None
    state_left: str | None = None
    state_right: str | None = None
    current_duration: float = 0.0
    target_duration: float | None = None
    is_holding: bool = False
    angles: dict[str, float] = Field(default_factory=dict)
    form_score: int = 100
    avg_form_score: int = 100
    form_grade: Grade = Grade.A
    feedback_alerts: list[FeedbackAlert] = Field(default_factory=list)
    rep_completed: bool = False


class WorkoutSummary(BaseModel):
    """Final session statistics generated upon stopping an exercise."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    exercise_name: str
    total_reps: int
    counter_left: int = 0
    counter_right: int = 0
    total_duration_sec: float
    avg_form_score: int
    final_grade: str


class ClientFrameMessage(BaseModel):
    """Inbound WebSocket message containing flat 33-landmark coordinate array."""

    model_config = ConfigDict(extra="ignore")

    action: Literal["frame", "start", "stop", "reset"] = "frame"
    exercise: str | None = None
    flat_landmarks: list[float] | None = None
    width: int = 1280
    height: int = 720
    timestamp_sec: float = 0.0
