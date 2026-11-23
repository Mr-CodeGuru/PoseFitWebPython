"""Biomechanical feedback rules and alert evaluation.

Feedback rule evaluators and alert models.
"""

from __future__ import annotations

from dataclasses import dataclass

from posefit.fsm import Condition, EvaluationContext
from posefit.schemas import FeedbackAlert, Severity


@dataclass(slots=True)
class FeedbackRule:
    """Biomechanical form evaluation heuristic rule."""

    name: str
    condition_str: str
    condition: Condition
    message: str
    severity: Severity = Severity.WARNING

    def evaluate(self, ctx: EvaluationContext) -> FeedbackAlert | None:
        """Evaluates whether the feedback rule condition is satisfied."""
        if self.condition.evaluate(ctx):
            return FeedbackAlert(
                name=self.name,
                message=self.message,
                severity=self.severity,
            )
        return None
