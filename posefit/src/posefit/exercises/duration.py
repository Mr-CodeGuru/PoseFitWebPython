"""Duration / isometric hold exercise kinematics analyzer (e.g. Plank, Wall Sit).

Isometric duration hold kinematics analyzer.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from posefit.config import (
    DEFAULT_HOLD_STATE,
    DEFAULT_TARGET_DURATION,
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


class DurationExercise(ExerciseAnalyzer):
    """Isometric hold duration exercise analyzer."""

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

        self.hold_state: str = (
            config.hold_state if config.hold_state is not None else DEFAULT_HOLD_STATE
        )
        self.target_duration: float = (
            config.target_duration
            if config.target_duration is not None
            else DEFAULT_TARGET_DURATION
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
        self.counter: int = 0
        self.current_duration: float = 0.0
        self.hold_start_time: float | None = None
        self.is_holding: bool = False
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

        ctx = EvaluationContext()
        ctx.angles.update(angles)
        ctx.coords.update(coords)

        # 1. Update State Machine
        self.fsm.update(ctx)

        # 2. Duration tracking
        self.rep_completed = False
        if self.fsm.current_state == self.hold_state:
            if not self.is_holding:
                self.hold_start_time = timestamp_sec
                self.is_holding = True
                self.current_duration = 0.0
            elif self.hold_start_time is not None:
                self.current_duration = timestamp_sec - self.hold_start_time
        else:
            self.is_holding = False
            if self.current_duration >= self.target_duration:
                self.counter += 1
                self.rep_completed = True
            self.current_duration = 0.0
            self.hold_start_time = None

        # 3. Feedback
        active_feedback: list[FeedbackAlert] = []
        for rule in self.feedback_rules:
            alert = rule.evaluate(ctx)
            if alert is not None:
                active_feedback.append(alert)
        self.current_feedback = active_feedback

        # 4. Form Scoring
        self.current_score = self.score_calc.calculate(
            ctx=ctx,
            last_rep_duration=None,
            active_feedback_count=len(self.current_feedback),
        )

        return self.get_status()

    def reset(self) -> None:
        self.smoother.reset()
        self.fsm.reset()
        self.counter = 0
        self.current_duration = 0.0
        self.hold_start_time = None
        self.is_holding = False
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
            current_duration=self.current_duration,
            target_duration=self.target_duration,
            is_holding=self.is_holding,
            angles=self.current_angles,
            form_score=self.current_score.score,
            avg_form_score=self.current_score.score,
            form_grade=self.current_score.grade,
            feedback_alerts=self.current_feedback,
            rep_completed=self.rep_completed,
        )
