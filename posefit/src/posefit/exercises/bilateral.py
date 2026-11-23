"""Bilateral exercise kinematics analyzer with independent limb state tracking (e.g. Hammer Curl).

Bilateral dual-chain kinematics analyzer.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from posefit.config import (
    DEFAULT_MIN_REP_DURATION,
    ExerciseConfig,
)
from posefit.exercises.base import ExerciseAnalyzer
from posefit.exercises.standard import StandardExercise
from posefit.feedback import FeedbackRule
from posefit.filters import TemporalSmoother
from posefit.fsm import ConditionParser, EvaluationContext, StateDefinition, StateMachine
from posefit.geometry import calculate_angle_2d
from posefit.schemas import ExerciseResult, FeedbackAlert, FormScoreBreakdown, Grade, Landmark
from posefit.scoring import FormScoreCalculator


class BilateralExercise(ExerciseAnalyzer):
    """Bilateral dual-chain repetition exercise analyzer (independent left/right tracking)."""

    def __init__(self, config: ExerciseConfig) -> None:
        self.config: ExerciseConfig = config
        self._name: str = config.name

        # 1. Parse angle definitions
        self.angles_def: dict[str, tuple[str, str, str]] = {}
        for name, angle_cfg in config.angles.items():
            if len(angle_cfg.points) == 3:
                self.angles_def[name] = (
                    angle_cfg.points[0],
                    angle_cfg.points[1],
                    angle_cfg.points[2],
                )

        # 2. Temporal smoother
        window = config.smoothing.window if config.smoothing else 3
        enabled = config.smoothing.enabled if config.smoothing else True
        self.smoother = TemporalSmoother(window_size=window, enabled=enabled)

        # 3. Setup dual FSMs (left and right)
        states_left: dict[str, StateDefinition] = {}
        states_right: dict[str, StateDefinition] = {}
        for state_name, state_cfg in config.states.items():
            cond_l = ConditionParser.parse_str(state_cfg.condition)
            cond_r = ConditionParser.parse_str(state_cfg.condition)
            states_left[state_name] = StateDefinition(
                name=state_name,
                condition_str=state_cfg.condition,
                condition=cond_l,
            )
            states_right[state_name] = StateDefinition(
                name=state_name,
                condition_str=state_cfg.condition,
                condition=cond_r,
            )

        self.fsm_left = StateMachine(state_order=config.state_order, states=states_left)
        self.fsm_right = StateMachine(state_order=config.state_order, states=states_right)

        # 4. Feedback rules
        self.feedback_rules: list[FeedbackRule] = []
        for fb_name, fb_cfg in config.feedback.items():
            cond = ConditionParser.parse_str(fb_cfg.condition)
            self.feedback_rules.append(
                FeedbackRule(
                    name=fb_name,
                    condition_str=fb_cfg.condition,
                    condition=cond,
                    message=fb_cfg.message,
                    severity=fb_cfg.severity,
                )
            )

        counter_cfg = config.counter
        self.trigger_state: str = counter_cfg.trigger_state if counter_cfg else "curl"
        self.from_state: str | None = counter_cfg.from_state if counter_cfg else None
        self.min_rep_duration: float = (
            config.min_rep_duration
            if config.min_rep_duration is not None
            else DEFAULT_MIN_REP_DURATION
        )

        tempo_min = config.tempo.min if config.tempo else 1.0
        tempo_max = config.tempo.max if config.tempo else 3.0
        ideal = config.ideal_angles or {}
        self.score_calc = FormScoreCalculator(
            ideal_angles=ideal,
            tempo_min=tempo_min,
            tempo_max=tempo_max,
        )

        # Runtime state
        self.counter_left: int = 0
        self.counter_right: int = 0
        self.last_count_time_left: float = 0.0
        self.last_count_time_right: float = 0.0
        self.current_angles: dict[str, float] = {}
        self.current_feedback: list[FeedbackAlert] = []
        self.current_score: FormScoreBreakdown = FormScoreBreakdown(
            score=100,
            grade=Grade.A,
            angle_penalty=0,
            tempo_penalty=0,
            feedback_penalty=0,
        )
        self.rep_completed: bool = False

    @property
    def name(self) -> str:
        return self._name

    def calculate_angles(self, coords: dict[str, tuple[int, int]]) -> dict[str, float]:
        angles: dict[str, float] = {}
        for angle_name, (p1_name, p2_name, p3_name) in self.angles_def.items():
            p1 = coords.get(p1_name)
            p2 = coords.get(p2_name)
            p3 = coords.get(p3_name)
            if p1 is not None and p2 is not None and p3 is not None:
                raw_angle = calculate_angle_2d(p1, p2, p3)
                smoothed_angle = self.smoother.smooth(angle_name, raw_angle)
                angles[angle_name] = smoothed_angle
        self.current_angles = dict(angles)
        return angles

    def process_frame(
        self,
        landmarks: Sequence[Landmark] | Sequence[float] | np.ndarray,
        frame_width: int,
        frame_height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        coords = StandardExercise.extract_coords(landmarks, frame_width, frame_height)
        angles = self.calculate_angles(coords)

        # 1. Build Left Context
        left_ctx = EvaluationContext(primary_angle_name="left")
        left_ctx.angles.update(angles)
        left_ctx.coords.update(coords)
        left_angle = (
            angles.get("left")
            or angles.get("left_angle")
            or angles.get("left_arm")
            or angles.get("left_leg")
            or angles.get("left_hip")
            or angles.get("primary")
            or 0.0
        )
        left_ctx.angles["angle"] = left_angle
        left_ctx.angles["left_angle"] = left_angle

        # 2. Build Right Context
        right_ctx = EvaluationContext(primary_angle_name="right")
        right_ctx.angles.update(angles)
        right_ctx.coords.update(coords)
        right_angle = (
            angles.get("right")
            or angles.get("right_angle")
            or angles.get("right_arm")
            or angles.get("right_leg")
            or angles.get("right_hip")
            or angles.get("right_side")
            or 0.0
        )
        right_ctx.angles["angle"] = right_angle
        right_ctx.angles["right_angle"] = right_angle

        # 3. Update State Machines
        _, left_changed = self.fsm_left.update(left_ctx)
        _, right_changed = self.fsm_right.update(right_ctx)

        # 4. Update Bilateral Counters
        left_counted = False
        right_counted = False

        left_from_valid = (
            self.fsm_left.prev_state == self.from_state if self.from_state is not None else True
        )
        if (
            left_changed
            and self.fsm_left.current_state == self.trigger_state
            and left_from_valid
            and (timestamp_sec - self.last_count_time_left) >= self.min_rep_duration
        ):
            self.counter_left += 1
            self.last_count_time_left = timestamp_sec
            left_counted = True

        right_from_valid = (
            self.fsm_right.prev_state == self.from_state if self.from_state is not None else True
        )
        if (
            right_changed
            and self.fsm_right.current_state == self.trigger_state
            and right_from_valid
            and (timestamp_sec - self.last_count_time_right) >= self.min_rep_duration
        ):
            self.counter_right += 1
            self.last_count_time_right = timestamp_sec
            right_counted = True

        self.rep_completed = left_counted or right_counted

        # 5. Feedback: evaluate for both Left and Right sides
        active_feedback: list[FeedbackAlert] = []
        for rule in self.feedback_rules:
            left_alert = rule.evaluate(left_ctx)
            right_alert = rule.evaluate(right_ctx)

            if left_alert is not None and right_alert is not None:
                active_feedback.append(
                    FeedbackAlert(
                        name=left_alert.name,
                        message=f"Both sides: {left_alert.message}",
                        severity=left_alert.severity,
                    )
                )
            elif left_alert is not None:
                active_feedback.append(
                    FeedbackAlert(
                        name=left_alert.name,
                        message=f"Left: {left_alert.message}",
                        severity=left_alert.severity,
                    )
                )
            elif right_alert is not None:
                active_feedback.append(
                    FeedbackAlert(
                        name=right_alert.name,
                        message=f"Right: {right_alert.message}",
                        severity=right_alert.severity,
                    )
                )

        self.current_feedback = active_feedback

        # 6. Form Scoring: average across both sides
        left_score = self.score_calc.calculate(left_ctx, None, len(self.current_feedback))
        right_score = self.score_calc.calculate(right_ctx, None, len(self.current_feedback))
        avg_score = (left_score.score + right_score.score) // 2
        self.current_score = FormScoreBreakdown(
            score=avg_score,
            grade=Grade.from_score(avg_score),
            angle_penalty=(left_score.angle_penalty + right_score.angle_penalty) // 2,
            tempo_penalty=(left_score.tempo_penalty + right_score.tempo_penalty) // 2,
            feedback_penalty=(left_score.feedback_penalty + right_score.feedback_penalty) // 2,
        )

        return self.get_status()

    def reset(self) -> None:
        self.smoother.reset()
        self.fsm_left.reset()
        self.fsm_right.reset()
        self.counter_left = 0
        self.counter_right = 0
        self.last_count_time_left = 0.0
        self.last_count_time_right = 0.0
        self.current_angles.clear()
        self.current_feedback.clear()
        self.rep_completed = False

    def get_status(self) -> ExerciseResult:
        total_counter = self.counter_left + self.counter_right
        return ExerciseResult(
            exercise_name=self._name,
            counter=total_counter,
            counter_left=self.counter_left,
            counter_right=self.counter_right,
            current_state=self.fsm_left.current_state,
            prev_state=self.fsm_left.prev_state,
            state_left=self.fsm_left.current_state,
            state_right=self.fsm_right.current_state,
            current_duration=0.0,
            target_duration=None,
            is_holding=False,
            angles=self.current_angles,
            form_score=self.current_score.score,
            avg_form_score=self.current_score.score,
            form_grade=self.current_score.grade,
            feedback_alerts=self.current_feedback,
            rep_completed=self.rep_completed,
        )
