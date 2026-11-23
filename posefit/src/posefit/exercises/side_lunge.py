"""side_lunge exercise module kinematic movement analyzer."""

from __future__ import annotations

from pathlib import Path

from posefit.config import load_exercise_config_from_yaml
from posefit.exercises.standard import StandardExercise


class SideLungeExercise(StandardExercise):
    """side_lunge exercise kinematics analyzer."""

    @classmethod
    def from_bundled(cls) -> SideLungeExercise:
        yaml_path = (
            Path(__file__).resolve().parent.parent / "assets" / "exercises" / "side_lunge.yaml"
        )
        if not yaml_path.exists():
            yaml_path = (
                Path(__file__).resolve().parents[4]
                / "crates"
                / "posefit-core"
                / "assets"
                / "exercises"
                / "side_lunge.yaml"
            )
        with open(yaml_path, encoding="utf-8") as f:
            cfg = load_exercise_config_from_yaml(f.read())
        return cls(cfg)
