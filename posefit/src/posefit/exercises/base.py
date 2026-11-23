"""ExerciseAnalyzer abstract base protocol and shared exercise infrastructure.

ExerciseAnalyzer abstract protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np

from posefit.schemas import ExerciseResult, Landmark


class ExerciseAnalyzer(ABC):
    """Abstract protocol for an exercise kinematics analyzer."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the exercise (e.g. 'squat', 'push_up')."""
        pass

    @abstractmethod
    def process_frame(
        self,
        landmarks: Sequence[Landmark] | Sequence[float] | np.ndarray,
        frame_width: int,
        frame_height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        """Ingests frame landmarks and evaluates kinematics, FSM, and form."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Resets counters, timers, and state machine memory."""
        pass

    @abstractmethod
    def get_status(self) -> ExerciseResult:
        """Returns the current state and metrics without processing a new frame."""
        pass
