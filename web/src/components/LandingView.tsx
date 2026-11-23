import React from 'react';
import { Camera, Shield, Cpu, ArrowRight } from 'lucide-react';
import type { ExerciseDefinition } from '../data/exercises';

interface LandingViewProps {
  exercises: ExerciseDefinition[];
  onStart: () => void;
  onSelectExercise: (id: string) => void;
  isEngineReady: boolean;
}

export const LandingView: React.FC<LandingViewProps> = ({
  exercises,
  onStart,
  onSelectExercise,
  isEngineReady,
}) => {
  return (
    <div className="w-full flex flex-col items-center">
      {/* Hero Section */}
      <section className="w-full max-w-5xl px-4 pt-12 pb-16 md:pt-20 md:pb-24 flex flex-col items-center text-center">
        {/* Technical Sub-badge */}
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded border border-[var(--border-strong)] bg-[var(--bg-card)] text-xs font-mono text-[var(--text-secondary)] mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>ON-DEVICE COMPUTER VISION — 0 LATENCY</span>
        </div>

        {/* Primary Functional Headline */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight text-[var(--text-primary)] max-w-3xl leading-[1.1]">
          Real-time exercise tracking and form feedback using your camera.
        </h1>

        {/* Crisp Literal Subtitle */}
        <p className="mt-5 text-sm sm:text-base text-[var(--text-secondary)] max-w-2xl leading-relaxed">
          PoseFit runs MediaPipe pose estimation with Python-optimized kinematic state machines directly inside your browser. Your video feed never leaves your device.
        </p>

        {/* Action Button */}
        <div className="mt-8 flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
          <button
            type="button"
            onClick={onStart}
            disabled={!isEngineReady}
            className="w-full sm:w-auto px-8 py-3.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm tracking-wide uppercase transition-colors rounded cursor-pointer disabled:opacity-50 flex items-center justify-center space-x-2"
          >
            <span>Start Workout</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Core Architecture Telemetry Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-3xl mt-14 text-left">
          <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-500 font-semibold mb-1">
              <Camera className="w-3.5 h-3.5" />
              <span>33-POINT SKELETON</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] leading-normal">
              Continuous sub-millisecond anatomical angle evaluation at full camera frame rate.
            </p>
          </div>

          <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-500 font-semibold mb-1">
              <Cpu className="w-3.5 h-3.5" />
              <span>PYTHON CV ENGINE</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] leading-normal">
              Deterministic state machines and scoring algorithms compiled from optimized Python.
            </p>
          </div>

          <div className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-500 font-semibold mb-1">
              <Shield className="w-3.5 h-3.5" />
              <span>100% PRIVATE</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] leading-normal">
              Camera frames are processed in local memory and instantly discarded. No server uploads.
            </p>
          </div>
        </div>
      </section>

      {/* Verified Movement Library Overview */}
      <section className="w-full max-w-6xl px-4 py-12 border-t border-[var(--border-subtle)]">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between mb-8 gap-2">
          <div>
            <span className="text-xs font-mono uppercase tracking-widest text-emerald-500 font-bold block mb-1">
              Supported Movements
            </span>
            <h2 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
              18 Kinematic Exercise Routines
            </h2>
          </div>
          <span className="text-xs text-[var(--text-muted)] font-mono">
            {exercises.length} calibrated routines ready
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {exercises.map((ex) => (
            <div
              key={ex.id}
              onClick={() => onSelectExercise(ex.id)}
              className="p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-colors cursor-pointer flex flex-col justify-between text-left group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-[var(--text-primary)] group-hover:text-emerald-500 transition-colors">
                    {ex.name}
                  </span>
                  <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[var(--border-subtle)] text-[var(--text-secondary)] border border-[var(--border-strong)]">
                    {ex.type === 'duration' ? 'HOLD' : 'REPS'}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
                  {ex.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
                <span>{ex.targetMuscles.slice(0, 2).join(', ')}</span>
                <span className="text-[var(--text-secondary)]">{ex.equipment}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
