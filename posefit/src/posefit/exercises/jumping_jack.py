"""jumping_jack exercise module kinematic movement analyzer."""

from __future__ import annotations

from pathlib import Path

from posefit.config import load_exercise_config_from_yaml
from posefit.exercises.standard import StandardExercise


class JumpingJackExercise(StandardExercise):
    """jumping_jack exercise kinematics analyzer."""

    @classmethod
    def from_bundled(cls) -> JumpingJackExercise:
        yaml_path = (
            Path(__file__).resolve().parent.parent / "assets" / "exercises" / "jumping_jack.yaml"
        )
        if not yaml_path.exists():
            yaml_path = (
                Path(__file__).resolve().parents[4]
                / "crates"
                / "posefit-core"
                / "assets"
                / "exercises"
                / "jumping_jack.yaml"
            )
        with open(yaml_path, encoding="utf-8") as f:
            cfg = load_exercise_config_from_yaml(f.read())
        return cls(cfg)
