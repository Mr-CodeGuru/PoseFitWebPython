import React, { useEffect } from 'react';
import confetti from 'canvas-confetti';
import {
  Trophy,
  Clock,
  Target,
  Award,
  RotateCcw,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import type { WorkoutSummary } from '../types/posefit';
import { EXERCISE_DATABASE } from './ExerciseSelector';

interface WorkoutSummaryModalProps {
  summary: WorkoutSummary;
  onDismiss: () => void;
}

export const WorkoutSummaryModal: React.FC<WorkoutSummaryModalProps> = ({
  summary,
  onDismiss,
}) => {
  useEffect(() => {
    // Dual celebratory confetti burst
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#10b981', '#38bdf8', '#fbbf24', '#a855f7'],
    });

    const timer = setTimeout(() => {
      confetti({
        particleCount: 60,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#10b981', '#34d399', '#6ee7b7'],
      });
      confetti({
        particleCount: 60,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#38bdf8', '#818cf8', '#c084fc'],
      });
    }, 400);

    return () => clearTimeout(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
  };

  const getGradeTheme = (grade: string) => {
    switch (grade.toUpperCase()) {
      case 'A':
        return {
          textColor: 'text-emerald-400',
          borderColor: 'border-emerald-500/50',
          bgColor: 'bg-emerald-500/10',
          glowColor: 'shadow-emerald-500/20',
          label: 'Olympic Mastery',
          subtext: 'Flawless posture and consistent repetition tempo.',
        };
      case 'B':
        return {
          textColor: 'text-sky-400',
          borderColor: 'border-sky-500/50',
          bgColor: 'bg-sky-500/10',
          glowColor: 'shadow-sky-500/20',
          label: 'Great Technique',
          subtext: 'Minor form deviations, solid execution overall.',
        };
      case 'C':
        return {
          textColor: 'text-amber-400',
          borderColor: 'border-amber-500/50',
          bgColor: 'bg-amber-500/10',
          glowColor: 'shadow-amber-500/20',
          label: 'Needs Refinement',
          subtext: 'Pay attention to depth and alignment feedback.',
        };
      case 'D':
      case 'F':
      default:
        return {
          textColor: 'text-rose-400',
          borderColor: 'border-rose-500/50',
          bgColor: 'bg-rose-500/10',
          glowColor: 'shadow-rose-500/20',
          label: 'Form Alert',
          subtext: 'Focus on full range of motion and joint stability.',
        };
    }
  };

  const gradeInfo = getGradeTheme(summary.final_grade);
  const exerciseMeta = EXERCISE_DATABASE[summary.exercise_name];
  const displayName = exerciseMeta?.name || summary.exercise_name.replace(/_/g, ' ');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/85 backdrop-blur-xl animate-fadeIn">
      <div className="w-full max-w-lg bg-gradient-to-b from-slate-900/95 via-slate-900/90 to-slate-950/95 border border-slate-800/90 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden ring-1 ring-white/10">
        {/* Glow Spheres */}
        <div className="absolute -top-32 -left-32 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-64 h-64 bg-sky-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 text-center">
          {/* Header Icon */}
          <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/40 text-emerald-400 mb-3 shadow-lg shadow-emerald-500/15">
            <Trophy className="w-8 h-8" />
          </div>

          <div className="flex items-center justify-center space-x-1 text-emerald-400 font-mono text-[11px] font-bold uppercase tracking-widest mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>SESSION SUMMARY</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-white capitalize">
            {displayName}
          </h2>

          {/* Grade Hero Display */}
          <div className="my-6 flex flex-col items-center">
            <div
              className={`w-28 h-28 rounded-3xl border-2 flex flex-col items-center justify-center ${gradeInfo.textColor} ${gradeInfo.borderColor} ${gradeInfo.bgColor} shadow-xl ${gradeInfo.glowColor} relative`}
            >
              <span className="text-5xl font-black tracking-tight leading-none">
                {summary.final_grade}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest opacity-80 mt-1">
                Form Grade
              </span>
            </div>
            <span className={`mt-3 font-bold text-sm tracking-wide ${gradeInfo.textColor}`}>
              {gradeInfo.label}
            </span>
            <p className="text-xs text-slate-400 max-w-xs mt-0.5">{gradeInfo.subtext}</p>
          </div>

          {/* Core Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col items-center">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <Target className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-semibold uppercase tracking-wider text-[10px]">
                  Total Reps
                </span>
              </div>
              <span className="text-2xl font-black text-white">{summary.total_reps}</span>
            </div>

            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col items-center">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <Award className="w-3.5 h-3.5 text-sky-400" />
                <span className="font-semibold uppercase tracking-wider text-[10px]">
                  Avg Score
                </span>
              </div>
              <span className="text-2xl font-black text-white">{summary.avg_form_score}%</span>
            </div>

            <div className="col-span-2 sm:col-span-1 bg-slate-950/70 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col items-center">
              <div className="flex items-center space-x-1.5 text-slate-400 text-xs mb-1">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-semibold uppercase tracking-wider text-[10px]">
                  Duration
                </span>
              </div>
              <span className="text-2xl font-black text-white">
                {formatTime(summary.total_duration_sec)}
              </span>
            </div>
          </div>

          {/* Bilateral Split if recorded */}
          {(summary.counter_left > 0 || summary.counter_right > 0) && (
            <div className="mb-6 p-3 rounded-2xl bg-slate-950/50 border border-slate-800 flex items-center justify-around text-xs">
              <div className="text-center">
                <span className="text-slate-400 text-[10px] uppercase font-bold">Left Side</span>
                <p className="text-lg font-black text-sky-400">{summary.counter_left} Reps</p>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-slate-400 text-[10px] uppercase font-bold">Right Side</span>
                <p className="text-lg font-black text-sky-400">{summary.counter_right} Reps</p>
              </div>
            </div>
          )}

          {/* Action Button */}
          <button
            type="button"
            onClick={onDismiss}
            className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-400 hover:to-teal-300 active:scale-98 text-slate-950 font-black rounded-2xl uppercase tracking-wider text-sm transition-all duration-150 flex items-center justify-center space-x-2 shadow-xl shadow-emerald-500/25 cursor-pointer ring-1 ring-white/20"
          >
            <RotateCcw className="w-4 h-4 stroke-[2.5]" />
            <span>Start Next Workout</span>
            <ChevronRight className="w-4 h-4 ml-1 stroke-[2.5]" />
          </button>
        </div>
      </div>
    </div>
  );
};
