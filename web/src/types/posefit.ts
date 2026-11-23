export type FormGrade = 'A' | 'B' | 'C' | 'D' | 'F';

export type AlertSeverity = 'critical' | 'warning' | 'info' | 'error';

export interface FeedbackAlert {
  name: string;
  message: string;
  severity: AlertSeverity;
}

export interface ExerciseResult {
  exercise_name: string;
  counter: number;
  counter_left: number;
  counter_right: number;
  current_state: string | null;
  prev_state: string | null;
  state_left: string | null;
  state_right: string | null;
  current_duration: number;
  target_duration: number | null;
  is_holding: boolean;
  angles: Record<string, number>;
  form_score: number;
  avg_form_score: number;
  form_grade: FormGrade;
  feedback_alerts: FeedbackAlert[];
  rep_completed: boolean;
}

export interface WorkoutSummary {
  exercise_name: string;
  total_reps: number;
  counter_left: number;
  counter_right: number;
  total_duration_sec: number;
  avg_form_score: number;
  final_grade: string;
}

export interface NormalizedLandmark {
  x: number;
  y: number;
  z: number;
  visibility?: number;
}
