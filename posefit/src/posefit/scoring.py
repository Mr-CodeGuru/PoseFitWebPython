"""Mathematical form scoring model and grade determination.

Deduction-based form scoring engine:
Form Score = max(0, min(100, 100 - (Angle Penalty + Tempo Penalty + Feedback Penalty)))
"""

from __future__ import annotations

from collections.abc import Mapping

from posefit.config import (
    ANGLE_PENALTY_DIVISOR,
    ANGLE_PENALTY_MULTIPLIER,
    BASE_FORM_SCORE,
    DEFAULT_TEMPO_MAX,
    DEFAULT_TEMPO_MIN,
    FEEDBACK_PENALTY_PER_ALERT,
    MAX_ANGLE_PENALTY,
    MAX_FEEDBACK_PENALTY,
    MAX_TEMPO_PENALTY,
    TEMPO_FAST_PENALTY_PER_STEP,
    TEMPO_FAST_STEP_SEC,
    TEMPO_SLOW_PENALTY_PER_SEC,
)
from posefit.fsm import EvaluationContext
from posefit.schemas import FormScoreBreakdown, Grade


class FormScoreCalculator:
    """Calculates instantaneous repetition form scores and grade breakdowns."""

    __slots__ = ("ideal_angles", "tempo_min", "tempo_max")

    def __init__(
        self,
        ideal_angles: Mapping[str, float] | None = None,
        tempo_min: float = DEFAULT_TEMPO_MIN,
        tempo_max: float = DEFAULT_TEMPO_MAX,
    ) -> None:
        self.ideal_angles: dict[str, float] = dict(ideal_angles or {})
        self.tempo_min: float = tempo_min
        self.tempo_max: float = tempo_max

    def calculate(
        self,
        ctx: EvaluationContext,
        last_rep_duration: float | None = None,
        active_feedback_count: int = 0,
    ) -> FormScoreBreakdown:
        score = BASE_FORM_SCORE

        # 1. Angle Penalty (max 40)
        angle_pen = min(MAX_ANGLE_PENALTY, self._calculate_angle_penalty(ctx))
        score -= angle_pen

        # 2. Tempo Penalty (max 30)
        tempo_pen = min(MAX_TEMPO_PENALTY, self._calculate_tempo_penalty(last_rep_duration))
        score -= tempo_pen

        # 3. Feedback Penalty (max 30)
        fb_pen = min(MAX_FEEDBACK_PENALTY, active_feedback_count * FEEDBACK_PENALTY_PER_ALERT)
        score -= fb_pen

        final_score = max(0, min(100, score))
        grade = Grade.from_score(final_score)

        return FormScoreBreakdown(
            score=final_score,
            grade=grade,
            angle_penalty=angle_pen,
            tempo_penalty=tempo_pen,
            feedback_penalty=fb_pen,
        )

    def _calculate_angle_penalty(self, ctx: EvaluationContext) -> int:
        if not self.ideal_angles:
            return 0

        total_deviation = 0.0
        count = 0

        for angle_name, ideal_val in self.ideal_angles.items():
            curr = ctx.get_var(angle_name)
            if curr is None:
                curr = ctx.get_var("angle")
            if curr is not None:
                deviation = abs(curr - ideal_val)
                total_deviation += (deviation / ANGLE_PENALTY_DIVISOR) * ANGLE_PENALTY_MULTIPLIER
                count += 1

        if count > 0:
            return int(total_deviation / count)
        return 0

    def _calculate_tempo_penalty(self, duration: float | None) -> int:
        if duration is None:
            return 0

        if duration < self.tempo_min:
            # Too fast: each 0.5s under min = 15 points
            return int(
                ((self.tempo_min - duration) / TEMPO_FAST_STEP_SEC) * TEMPO_FAST_PENALTY_PER_STEP
            )
        if duration > self.tempo_max:
            # Too slow: each 1s over max = 10 points
            return int((duration - self.tempo_max) * TEMPO_SLOW_PENALTY_PER_SEC)

        return 0
