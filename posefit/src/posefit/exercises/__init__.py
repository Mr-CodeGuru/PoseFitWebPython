"""Exercise analyzers catalog, factory loader, and concrete exercise classes.

Exercise catalog and factory.
"""

from __future__ import annotations

from pathlib import Path

from posefit.config import ExerciseConfig, ExerciseKind, load_exercise_config_from_yaml
from posefit.exercises.base import ExerciseAnalyzer
from posefit.exercises.bilateral import BilateralExercise
from posefit.exercises.duration import DurationExercise
from posefit.exercises.standard import StandardExercise

__all__ = [
    "ExerciseAnalyzer",
    "StandardExercise",
    "BilateralExercise",
    "DurationExercise",
    "create_exercise",
    "load_exercise_from_yaml_file",
]


def create_exercise(config: ExerciseConfig) -> ExerciseAnalyzer:
    """Factory creating concrete ExerciseAnalyzer."""
    if config.type == ExerciseKind.DURATION:
        return DurationExercise(config)
    if config.bilateral:
        return BilateralExercise(config)
    return StandardExercise(config)


def load_exercise_from_yaml_file(yaml_path: str | Path) -> ExerciseAnalyzer:
    """Loads exercise configuration from file and creates analyzer."""
    with open(yaml_path, encoding="utf-8") as f:
        config = load_exercise_config_from_yaml(f.read())
    return create_exercise(config)
