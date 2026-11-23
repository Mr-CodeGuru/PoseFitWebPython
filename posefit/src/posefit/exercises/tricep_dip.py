"""tricep_dip exercise module kinematic movement analyzer."""

from __future__ import annotations

from pathlib import Path

from posefit.config import load_exercise_config_from_yaml
from posefit.exercises.standard import StandardExercise


class TricepDipExercise(StandardExercise):
    """tricep_dip exercise kinematics analyzer."""

    @classmethod
    def from_bundled(cls) -> TricepDipExercise:
        yaml_path = (
            Path(__file__).resolve().parent.parent / "assets" / "exercises" / "tricep_dip.yaml"
        )
        if not yaml_path.exists():
            yaml_path = (
                Path(__file__).resolve().parents[4]
                / "crates"
                / "posefit-core"
                / "assets"
                / "exercises"
                / "tricep_dip.yaml"
            )
        with open(yaml_path, encoding="utf-8") as f:
            cfg = load_exercise_config_from_yaml(f.read())
        return cls(cfg)
