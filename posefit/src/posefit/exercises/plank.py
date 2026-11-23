"""plank exercise module kinematic movement analyzer."""

from __future__ import annotations

from pathlib import Path

from posefit.config import load_exercise_config_from_yaml
from posefit.exercises.duration import DurationExercise


class PlankExercise(DurationExercise):
    """plank exercise kinematics analyzer."""

    @classmethod
    def from_bundled(cls) -> PlankExercise:
        yaml_path = (
            Path(__file__).resolve().parent.parent / "assets" / "exercises" / "plank.yaml"
        )
        if not yaml_path.exists():
            yaml_path = (
                Path(__file__).resolve().parents[4]
                / "crates"
                / "posefit-core"
                / "assets"
                / "exercises"
                / "plank.yaml"
            )
        with open(yaml_path, encoding="utf-8") as f:
            cfg = load_exercise_config_from_yaml(f.read())
        return cls(cfg)
