import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Activity } from 'lucide-react';
import type { ExerciseDefinition } from '../data/exercises';

interface ChooseExerciseViewProps {
  exercises: ExerciseDefinition[];
  selectedExerciseId: string;
  onSelect: (id: string) => void;
  onConfirm: () => void;
  onBack: () => void;
}

export const ChooseExerciseView: React.FC<ChooseExerciseViewProps> = ({
  exercises,
  selectedExerciseId,
  onSelect,
  onConfirm,
  onBack,
}) => {
  const [filter, setFilter] = useState<'all' | 'reps' | 'duration' | 'bilateral'>('all');

  const filtered = exercises.filter((ex) => {
    if (filter === 'reps') return ex.type === 'repetition';
    if (filter === 'duration') return ex.type === 'duration';
    if (filter === 'bilateral') return ex.bilateral;
    return true;
  });

  const selectedExercise = exercises.find((e) => e.id === selectedExerciseId) || exercises[0];

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-8">
      {/* Header Bar */}
      <div className="flex items-center justify-between pb-6 border-b border-[var(--border-subtle)]">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO OVERVIEW</span>
        </button>

        <span className="text-xs font-mono text-[var(--text-muted)]">STEP 1 OF 3</span>
      </div>

      <div className="mt-8 flex flex-col lg:flex-row gap-8 items-start">
        {/* Left: Exercise Grid Selection */}
        <div className="flex-1 w-full">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-black tracking-tight text-[var(--text-primary)] uppercase">
                Choose Movement
              </h1>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Select an exercise to calibrate camera joint tracking and state machines.
              </p>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center space-x-1 p-1 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] text-xs font-mono">
              {(
                [
                  { id: 'all', label: 'ALL' },
                  { id: 'reps', label: 'REPETITION' },
                  { id: 'duration', label: 'ISOMETRIC' },
                  { id: 'bilateral', label: 'BILATERAL' },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilter(tab.id)}
                  className={`px-3 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                    filter === tab.id
                      ? 'bg-[var(--border-strong)] text-[var(--text-primary)] border border-[var(--border-strong)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {filtered.map((ex) => {
              const isSelected = ex.id === selectedExerciseId;
              return (
                <button
                  key={ex.id}
                  type="button"
                  onClick={() => onSelect(ex.id)}
                  className={`p-3.5 rounded border text-left transition-colors cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'border-emerald-500 bg-[var(--bg-card)] ring-1 ring-emerald-500'
                      : 'border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)]'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-mono text-emerald-500 uppercase tracking-wider block">
                        {ex.difficulty}
                      </span>
                      <h3 className="text-sm font-bold text-[var(--text-primary)] mt-0.5">{ex.name}</h3>
                    </div>
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
                    <span>{ex.targetMuscles[0]}</span>
                    <span>{ex.type === 'duration' ? 'HOLD' : 'REPS'}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Exercise Detailed Specification Card */}
        {selectedExercise && (
          <div className="w-full lg:w-80 shrink-0 border border-[var(--border-subtle)] rounded bg-[var(--bg-card)] p-5 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-emerald-500 font-bold uppercase mb-2">
                <Activity className="w-3.5 h-3.5" />
                <span>CALIBRATION PROFILE</span>
              </div>

              <h2 className="text-xl font-black text-[var(--text-primary)]">{selectedExercise.name}</h2>
              <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
                {selectedExercise.description}
              </p>

              <div className="mt-6 space-y-3 text-xs border-t border-[var(--border-subtle)] pt-4">
                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)] font-mono">
                  <span className="text-[var(--text-muted)]">TYPE:</span>
                  <span className="text-[var(--text-primary)] uppercase font-bold">{selectedExercise.type}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)] font-mono">
                  <span className="text-[var(--text-muted)]">BILATERAL:</span>
                  <span className="text-[var(--text-primary)] uppercase font-bold">
                    {selectedExercise.bilateral ? 'YES (BOTH SIDES)' : 'STANDARD'}
                  </span>
                </div>

                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)] font-mono">
                  <span className="text-[var(--text-muted)]">EQUIPMENT:</span>
                  <span className="text-[var(--text-primary)] uppercase font-bold">{selectedExercise.equipment}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-[var(--border-subtle)] font-mono">
                  <span className="text-[var(--text-muted)]">TARGET:</span>
                  <span className="text-emerald-500 uppercase font-bold">
                    {selectedExercise.type === 'duration'
                      ? `${selectedExercise.targetDuration || 30} SECONDS`
                      : `${selectedExercise.defaultReps} REPS`}
                  </span>
                </div>

                <div className="pt-2">
                  <span className="text-[11px] font-mono text-[var(--text-muted)] uppercase block mb-1.5">
                    Engaged Muscles:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {selectedExercise.targetMuscles.map((muscle) => (
                      <span
                        key={muscle}
                        className="px-2 py-0.5 rounded bg-[var(--border-subtle)] border border-[var(--border-strong)] text-[var(--text-secondary)] text-[10px] font-mono"
                      >
                        {muscle}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onConfirm}
              className="mt-8 w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider rounded transition-colors flex items-center justify-center space-x-2 cursor-pointer"
            >
              <span>Continue to Setup</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
