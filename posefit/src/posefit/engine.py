"""PoseFit Core Engine - Pure computation layer coordinating kinematics, FSM, and exercise sessions.

Zero web imports, zero I/O on the hot path.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from posefit.config import (
    ExerciseConfig,
    get_bundled_assets_dir,
    load_exercise_config_from_yaml,
)
from posefit.exercises import ExerciseAnalyzer, create_exercise
from posefit.schemas import ExerciseResult, Landmark, WorkoutSummary


class PoseEstimator(Protocol):
    """Protocol abstracting on-device pose estimation neural networks (Mode B)."""

    def estimate(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
    ) -> list[Landmark]:
        """Runs inference on raw image buffer and returns 33 landmarks."""
        ...


class MockPoseEstimator:
    """Deterministic mock pose estimator for testing and validation."""

    def __init__(self, next_landmarks: list[Landmark] | None = None) -> None:
        if next_landmarks is not None:
            self.next_landmarks = next_landmarks
        else:
            self.next_landmarks = [Landmark(x=0.0, y=0.0, z=0.0) for _ in range(33)]

    def estimate(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
    ) -> list[Landmark]:
        return list(self.next_landmarks)


class PoseEngine:
    """Central kinematics engine coordinating exercise tracking, FSM evaluation, and form scoring.

    Main kinematics engine.
    Pure class with zero I/O in the frame processing loop.
    """

    def __init__(self) -> None:
        self.configs: dict[str, ExerciseConfig] = {}
        self.active_exercise: ExerciseAnalyzer | None = None
        self.estimator: PoseEstimator | None = None
        self.workout_start_time: float | None = None
        self.workout_last_time: float | None = None

    def register_exercise_yaml(self, yaml_str: str) -> None:
        """Registers a single exercise from a YAML configuration string."""
        config = load_exercise_config_from_yaml(yaml_str)
        self.configs[config.name] = config

    def register_all_bundled_exercises(self, assets_dir: Path | None = None) -> None:
        """Loads and registers all 18 bundled exercise definitions."""
        target_dir = assets_dir or get_bundled_assets_dir()
        if not target_dir.exists():
            raise FileNotFoundError(f"Exercise assets directory not found at {target_dir}")

        yaml_files = sorted(target_dir.glob("*.yaml"))
        if not yaml_files:
            raise FileNotFoundError(f"No YAML exercise definitions found in {target_dir}")

        for yaml_path in yaml_files:
            with open(yaml_path, encoding="utf-8") as f:
                self.register_exercise_yaml(f.read())

    def available_exercises(self) -> list[str]:
        """Returns sorted list of names for all registered exercises."""
        return sorted(self.configs.keys())

    def start_exercise(self, exercise_name: str) -> None:
        """Starts or switches tracking to the specified exercise."""
        if exercise_name not in self.configs:
            raise KeyError(f"Exercise not found: '{exercise_name}'")

        config = self.configs[exercise_name]
        self.active_exercise = create_exercise(config)
        self.workout_start_time = None
        self.workout_last_time = None

    def process_landmarks(
        self,
        landmarks: Sequence[Landmark] | Sequence[float] | np.ndarray,
        width: int,
        height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        """Ingests frame landmarks, updates FSM, counting, and form scoring."""
        if self.workout_start_time is None:
            self.workout_start_time = timestamp_sec
        self.workout_last_time = timestamp_sec

        if self.active_exercise is None:
            raise RuntimeError("No active exercise running. Call start_exercise() first.")

        return self.active_exercise.process_frame(landmarks, width, height, timestamp_sec)

    def process_landmarks_flat(
        self,
        flat_data: Sequence[float] | np.ndarray,
        width: int,
        height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        """Ingests flat coordinate array [x0, y0, ...], matching WASM processLandmarksFlat."""
        if len(flat_data) < 33 * 4:
            raise ValueError(
                f"Landmark flat buffer must contain at least 132 elements (got {len(flat_data)})"
            )
        return self.process_landmarks(flat_data, width, height, timestamp_sec)

    def process_image_bytes(
        self,
        image_bytes: bytes,
        width: int,
        height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        """Ingests raw image bytes, runs pose estimator (Mode B), and updates kinematics."""
        if self.estimator is None:
            raise RuntimeError(
                "No PoseEstimator configured. Call set_estimator() or with_estimator() first."
            )
        landmarks = self.estimator.estimate(image_bytes, width, height)
        return self.process_landmarks(landmarks, width, height, timestamp_sec)

    def stop_exercise(self) -> WorkoutSummary:
        """Stops the active exercise session and computes final summary metrics."""
        if self.active_exercise is None:
            raise RuntimeError("No active exercise running. Call start_exercise() first.")

        status = self.active_exercise.get_status()
        self.active_exercise = None

        start_t = self.workout_start_time if self.workout_start_time is not None else 0.0
        end_t = self.workout_last_time if self.workout_last_time is not None else start_t
        total_duration = max(0.0, end_t - start_t)

        return WorkoutSummary(
            exercise_name=status.exercise_name,
            total_reps=status.counter,
            counter_left=status.counter_left,
            counter_right=status.counter_right,
            total_duration_sec=total_duration,
            avg_form_score=status.avg_form_score,
            final_grade=status.form_grade.value,
        )

    def reset(self) -> None:
        """Resets the currently active exercise counters and state machines."""
        if self.active_exercise is not None:
            self.active_exercise.reset()
        self.workout_start_time = None
        self.workout_last_time = None

    def status(self) -> ExerciseResult | None:
        """Gets the current exercise status without processing a new frame."""
        if self.active_exercise is not None:
            return self.active_exercise.get_status()
        return None

    def set_estimator(self, estimator: PoseEstimator) -> None:
        """Configures the pose estimator for Mode B."""
        self.estimator = estimator

    def with_estimator(self, estimator: PoseEstimator) -> PoseEngine:
        """Fluent builder method setting the pose estimator."""
        self.estimator = estimator
        return self
