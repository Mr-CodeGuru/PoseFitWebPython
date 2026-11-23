"""PoseFit Python Core - Pure-Python kinematics engine, FSM, and local-first server."""

from posefit.engine import PoseEngine
from posefit.schemas import ExerciseResult, FeedbackAlert, Landmark, WorkoutSummary

__all__ = [
    "PoseEngine",
    "ExerciseResult",
    "WorkoutSummary",
    "Landmark",
    "FeedbackAlert",
]

__version__ = "0.1.0"
