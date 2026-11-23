import React from 'react';
import {
  RotateCcw,
  ArrowRight,
  Target,
  Award,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import type { WorkoutSummary } from '../types/posefit';
import { EXERCISE_MAP } from '../data/exercises';

interface ResultsViewProps {
  summary: WorkoutSummary;
  onWorkoutAgain: () => void;
  onChooseAnother: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  summary,
  onWorkoutAgain,
  onChooseAnother,
}) => {
  const exercise = EXERCISE_MAP[summary.exercise_name];
  const displayName = exercise?.name || summary.exercise_name.replace(/_/g, ' ');

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
  };

  const getGradeTheme = (grade: string) => {
    switch (grade.toUpperCase()) {
      case 'A':
        return {
          textColor: 'text-emerald-500',
          borderColor: 'border-emerald-500',
          label: 'EXCELLENT FORM',
          description: 'Joint angles adhered to ideal kinematic thresholds throughout the set.',
        };
      case 'B':
        return {
          textColor: 'text-sky-500',
          borderColor: 'border-sky-500',
          label: 'SOLID EXECUTION',
          description: 'Minor form deviations detected. Maintained stability during transitions.',
        };
      case 'C':
        return {
          textColor: 'text-amber-500',
          borderColor: 'border-amber-500',
          label: 'FORM DEVIATIONS',
          description: 'Notable angle penalties recorded. Check posture alerts during next set.',
        };
      case 'D':
      case 'F':
      default:
        return {
          textColor: 'text-rose-500',
          borderColor: 'border-rose-500',
          label: 'CRITICAL ERRORS',
          description: 'Incomplete range of motion or joint misalignment detected.',
        };
    }
  };

  const theme = getGradeTheme(summary.final_grade);

  return (
    <div className="w-full max-w-3xl mx-auto px-4 py-12 flex flex-col items-center">
      {/* Top Completion Header */}
      <div className="w-full text-center pb-8 border-b border-[var(--border-subtle)]">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] text-xs font-mono text-emerald-500 mb-4 shadow-sm">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>SESSION TELEMETRY LOGGED</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text-primary)] tracking-tight uppercase">
          {displayName} Summary
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1 font-mono">
          Python kinematic evaluation finished
        </p>
      </div>

      {/* Grade & Score Banner */}
      <div className="w-full my-8 p-6 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
        <div className="flex items-center space-x-6">
          <div
            className={`w-20 h-20 rounded border-2 ${theme.borderColor} bg-[var(--bg-card-solid)] flex flex-col items-center justify-center font-mono`}
          >
            <span className={`text-4xl font-black ${theme.textColor}`}>
              {summary.final_grade}
            </span>
            <span className="text-[9px] uppercase font-bold text-[var(--text-muted)]">GRADE</span>
          </div>

          <div>
            <span className={`text-sm font-bold font-mono uppercase ${theme.textColor}`}>
              {theme.label}
            </span>
            <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-sm leading-relaxed">
              {theme.description}
            </p>
          </div>
        </div>

        <div className="text-right sm:border-l sm:border-[var(--border-subtle)] sm:pl-6">
          <span className="text-xs font-mono text-[var(--text-muted)] uppercase block">AVERAGE SCORE</span>
          <span className="text-4xl font-black text-[var(--text-primary)] font-mono">
            {summary.avg_form_score}%
          </span>
        </div>
      </div>

      {/* Verified Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full mb-8">
        <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] shadow-sm">
          <div className="flex items-center space-x-1.5 text-[var(--text-secondary)] text-xs font-mono mb-1">
            <Target className="w-3.5 h-3.5 text-emerald-500" />
            <span>TOTAL REPS</span>
          </div>
          <span className="text-2xl font-black text-[var(--text-primary)] font-mono">{summary.total_reps}</span>
        </div>

        <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] shadow-sm">
          <div className="flex items-center space-x-1.5 text-[var(--text-secondary)] text-xs font-mono mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-500" />
            <span>SET DURATION</span>
          </div>
          <span className="text-2xl font-black text-[var(--text-primary)] font-mono">
            {formatDuration(summary.total_duration_sec)}
          </span>
        </div>

        <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] shadow-sm">
          <div className="flex items-center space-x-1.5 text-[var(--text-secondary)] text-xs font-mono mb-1">
            <Award className="w-3.5 h-3.5 text-sky-500" />
            <span>DIFFICULTY</span>
          </div>
          <span className="text-2xl font-black text-[var(--text-primary)] font-mono capitalize">
            {exercise?.difficulty || 'Beginner'}
          </span>
        </div>
      </div>

      {/* Bilateral Split Breakdown (Only if bilateral limbs recorded) */}
      {(summary.counter_left > 0 || summary.counter_right > 0) && (
        <div className="w-full mb-8 p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] flex items-center justify-around font-mono text-xs shadow-sm">
          <div className="text-center">
            <span className="text-[var(--text-muted)] uppercase block mb-1">Left Side Reps</span>
            <span className="text-xl font-bold text-sky-500">{summary.counter_left}</span>
          </div>
          <div className="w-px h-8 bg-[var(--border-subtle)]" />
          <div className="text-center">
            <span className="text-[var(--text-muted)] uppercase block mb-1">Right Side Reps</span>
            <span className="text-xl font-bold text-sky-500">{summary.counter_right}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="w-full flex flex-col sm:flex-row gap-3 pt-6 border-t border-[var(--border-subtle)]">
        <button
          type="button"
          onClick={onWorkoutAgain}
          className="flex-1 py-3 px-6 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider rounded transition-colors flex items-center justify-center space-x-2 cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Workout Again</span>
        </button>

        <button
          type="button"
          onClick={onChooseAnother}
          className="flex-1 py-3 px-6 bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-bold text-xs uppercase tracking-wider rounded transition-colors flex items-center justify-center space-x-2 cursor-pointer"
        >
          <span>Choose Another Movement</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
