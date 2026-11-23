"""Standard repetition-based exercise kinematics analyzer (e.g. Squat, Push-up).

Standard repetition kinematics analyzer.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from posefit.config import (
    DEFAULT_MIN_REP_DURATION,
    LANDMARK_NAME_TO_INDEX,
    CounterConfig,
    ExerciseConfig,
)
from posefit.exercises.base import ExerciseAnalyzer
from posefit.feedback import FeedbackRule
from posefit.filters import TemporalSmoother
from posefit.fsm import ConditionParser, EvaluationContext, StateDefinition, StateMachine
from posefit.geometry import calculate_angle_2d
from posefit.schemas import ExerciseResult, FeedbackAlert, FormScoreBreakdown, Grade, Landmark
from posefit.scoring import FormScoreCalculator


class StandardExercise(ExerciseAnalyzer):
    """Standard single-chain repetition exercise analyzer."""

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

        # 2. Setup temporal smoother
        window = config.smoothing.window if config.smoothing else 3
        enabled = config.smoothing.enabled if config.smoothing else True
        self.smoother = TemporalSmoother(window_size=window, enabled=enabled)

        # 3. Setup FSM
        states: dict[str, StateDefinition] = {}
        for state_name, state_cfg in config.states.items():
            cond = ConditionParser.parse_str(state_cfg.condition)
            states[state_name] = StateDefinition(
                name=state_name,
                condition_str=state_cfg.condition,
                condition=cond,
            )
        self.fsm = StateMachine(state_order=config.state_order, states=states)

        # 4. Setup feedback rules
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

        # 5. Form scoring calculator
        tempo_min = config.tempo.min if config.tempo else 1.0
        tempo_max = config.tempo.max if config.tempo else 3.0
        ideal = config.ideal_angles or {}
        self.score_calc = FormScoreCalculator(
            ideal_angles=ideal,
            tempo_min=tempo_min,
            tempo_max=tempo_max,
        )

        self.min_rep_duration: float = (
            config.min_rep_duration
            if config.min_rep_duration is not None
            else DEFAULT_MIN_REP_DURATION
        )
        self.counter_rule: CounterConfig | None = config.counter

        # Runtime state
        self.counter: int = 0
        self.last_count_time: float = 0.0
        self.rep_start_time: float | None = None
        self.rep_durations: list[float] = []
        self.rep_form_scores: list[int] = []
        self.avg_form_score: int = 100
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

    @staticmethod
    def extract_coords(
        landmarks: Sequence[Landmark] | Sequence[float] | np.ndarray,
        width: int,
        height: int,
    ) -> dict[str, tuple[int, int]]:
        """Converts landmarks to pixel coordinate dictionary."""
        coords: dict[str, tuple[int, int]] = {}

        # Handle flat float array [x0, y0, z0, v0, ...]
        if isinstance(landmarks, (list, tuple, np.ndarray)) and len(landmarks) > 0:
            first = landmarks[0]
            if isinstance(first, (int, float, np.floating)):
                for name, idx in LANDMARK_NAME_TO_INDEX.items():
                    offset = idx * 4
                    if offset + 1 < len(landmarks):
                        coords[name] = (
                            int(landmarks[offset] * width),
                            int(landmarks[offset + 1] * height),
                        )
                return coords

        # Handle list of Landmark objects
        for name, idx in LANDMARK_NAME_TO_INDEX.items():
            if idx < len(landmarks):
                lm = landmarks[idx]
                if isinstance(lm, Landmark):
                    coords[name] = lm.to_pixel_coords(width, height)
                elif hasattr(lm, "x") and hasattr(lm, "y"):
                    coords[name] = (int(lm.x * width), int(lm.y * height))
        return coords

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

    def build_context(
        self,
        angles: dict[str, float],
        coords: dict[str, tuple[int, int]],
    ) -> EvaluationContext:
        ctx = EvaluationContext(primary_angle_name="primary")
        ctx.angles.update(angles)
        ctx.coords.update(coords)
        return ctx

    def process_frame(
        self,
        landmarks: Sequence[Landmark] | Sequence[float] | np.ndarray,
        frame_width: int,
        frame_height: int,
        timestamp_sec: float,
    ) -> ExerciseResult:
        coords = self.extract_coords(landmarks, frame_width, frame_height)
        angles = self.calculate_angles(coords)
        ctx = self.build_context(angles, coords)

        # 1. Update State Machine
        current_state, state_changed = self.fsm.update(ctx)

        if (
            state_changed
            and self.counter_rule is not None
            and self.counter_rule.from_state is not None
            and current_state == self.counter_rule.from_state
        ):
            self.rep_start_time = timestamp_sec

        # 2. Feedback evaluation
        active_feedback: list[FeedbackAlert] = []
        for rule in self.feedback_rules:
            alert = rule.evaluate(ctx)
            if alert is not None:
                active_feedback.append(alert)
        self.current_feedback = active_feedback

        # 3. Form Scoring
        last_rep_duration = self.rep_durations[-1] if self.rep_durations else None
        self.current_score = self.score_calc.calculate(
            ctx=ctx,
            last_rep_duration=last_rep_duration,
            active_feedback_count=len(self.current_feedback),
        )

        # 4. Counter evaluation (strictly on state_changed == True)
        self.rep_completed = False
        if state_changed and self.counter_rule is not None:
            reached_trigger = self.fsm.current_state == self.counter_rule.trigger_state

            if reached_trigger:
                from_valid = (
                    self.fsm.prev_state == self.counter_rule.from_state
                    if self.counter_rule.from_state is not None
                    else True
                )
                time_valid = (timestamp_sec - self.last_count_time) >= self.min_rep_duration

                if from_valid and time_valid:
                    self.counter += 1
                    self.last_count_time = timestamp_sec
                    self.rep_completed = True

                    if self.rep_start_time is not None:
                        duration = timestamp_sec - self.rep_start_time
                        self.rep_durations.append(duration)
                        self.rep_start_time = None

                    self.rep_form_scores.append(self.current_score.score)
                    if self.rep_form_scores:
                        self.avg_form_score = int(
                            sum(self.rep_form_scores) / len(self.rep_form_scores)
                        )

        return self.get_status()

    def reset(self) -> None:
        self.smoother.reset()
        self.fsm.reset()
        self.counter = 0
        self.last_count_time = 0.0
        self.rep_start_time = None
        self.rep_durations.clear()
        self.rep_form_scores.clear()
        self.avg_form_score = 100
        self.current_angles.clear()
        self.current_feedback.clear()
        self.rep_completed = False

    def get_status(self) -> ExerciseResult:
        return ExerciseResult(
            exercise_name=self._name,
            counter=self.counter,
            counter_left=0,
            counter_right=0,
            current_state=self.fsm.current_state,
            prev_state=self.fsm.prev_state,
            state_left=None,
            state_right=None,
            current_duration=0.0,
            target_duration=None,
            is_holding=False,
            angles=self.current_angles,
            form_score=self.current_score.score,
            avg_form_score=self.avg_form_score,
            form_grade=self.current_score.grade,
            feedback_alerts=self.current_feedback,
            rep_completed=self.rep_completed,
        )
