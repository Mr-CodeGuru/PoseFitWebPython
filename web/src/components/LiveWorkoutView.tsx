import React, { useRef, useState } from 'react';
import {
  Volume2,
  VolumeX,
  FlipHorizontal,
  RotateCcw,
  Square,
  AlertTriangle,
  Play,
  Pause,
  Repeat,
  Maximize2,
  Minimize2,
  X,
  Info,
} from 'lucide-react';
import type { ExerciseResult } from '../types/posefit';
import type { ExerciseDefinition } from '../data/exercises';

interface LiveWorkoutViewProps {
  exercise: ExerciseDefinition;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  exerciseResult: ExerciseResult | null;
  videoMode: 'camera' | 'recorded';
  videoFileName: string | null;
  isPlaying: boolean;
  isLooping: boolean;
  isEnded: boolean;
  currentTime: number;
  duration: number;
  isMuted: boolean;
  isMirrored: boolean;
  playbackSpeed: number;
  repBumpAnimation: boolean;
  activeAlert: { message: string; severity: string } | null;
  onTogglePlayPause: () => void;
  onToggleLoop: () => void;
  onReplay: () => void;
  onSeek: (time: number) => void;
  onSpeedChange: (speed: number) => void;
  onToggleMirror: () => void;
  onToggleMute: () => void;
  onResetCounter: () => void;
  onStopWorkout: () => void;
  onCloseSession: () => void;
}

export const LiveWorkoutView: React.FC<LiveWorkoutViewProps> = ({
  exercise,
  videoRef,
  canvasRef,
  exerciseResult,
  videoMode,
  videoFileName,
  isPlaying,
  isLooping,
  isEnded,
  currentTime,
  duration,
  isMuted,
  isMirrored,
  playbackSpeed,
  repBumpAnimation,
  activeAlert,
  onTogglePlayPause,
  onToggleLoop,
  onReplay,
  onSeek,
  onSpeedChange,
  onToggleMirror,
  onToggleMute,
  onResetCounter,
  onStopWorkout,
  onCloseSession,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showGuide, setShowGuide] = useState(false);

  const toggleFullscreen = () => {
    const el = containerRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen().catch(console.error);
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(console.error);
      setIsFullscreen(false);
    }
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const isDuration = exercise.type === 'duration';

  // Get qualitative score label
  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'EXCELLENT';
    if (score >= 75) return 'GOOD FORM';
    if (score >= 60) return 'SUB-OPTIMAL';
    return 'FORM ALERT';
  };

  const currentScore = exerciseResult?.form_score ?? 100;
  const scoreLabel = getScoreLabel(currentScore);

  return (
    <div className="w-full flex-1 flex flex-col items-center justify-center p-2 sm:p-4 md:p-6 max-w-7xl mx-auto">
      {/* Top Telemetry Header Bar */}
      <div className="w-full flex items-center justify-between pb-3 mb-2 border-b border-[var(--border-subtle)]">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <h1 className="text-base sm:text-lg font-black text-[var(--text-primary)] uppercase tracking-tight">
              {exercise.name}
            </h1>
          </div>
          <span className="text-xs font-mono text-[var(--text-muted)]">|</span>
          <span className="text-xs font-mono uppercase text-[var(--text-secondary)]">
            {videoMode === 'camera' ? 'LIVE CAMERA' : 'VIDEO FILE'}
          </span>
        </div>

        {/* Header Action Controls */}
        <div className="flex items-center space-x-1.5 sm:space-x-2">
          <button
            type="button"
            onClick={() => setShowGuide(!showGuide)}
            className="p-2 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors cursor-pointer"
            title="Biomechanics Guide"
          >
            <Info className="w-4 h-4 text-emerald-500" />
          </button>

          <button
            type="button"
            onClick={onToggleMirror}
            className={`p-2 rounded border transition-colors cursor-pointer ${
              isMirrored
                ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500'
                : 'border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            title="Mirror Video"
          >
            <FlipHorizontal className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onToggleMute}
            className={`p-2 rounded border transition-colors cursor-pointer ${
              !isMuted
                ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500'
                : 'border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>

          <button
            type="button"
            onClick={onResetCounter}
            className="p-2 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors cursor-pointer"
            title="Reset Counter"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={onStopWorkout}
            className="px-3 py-1.5 rounded border border-rose-500/40 bg-rose-500/10 text-rose-500 font-bold text-xs uppercase tracking-wider hover:bg-rose-500/20 transition-colors flex items-center space-x-1.5 cursor-pointer"
            title="Stop and view results"
          >
            <Square className="w-3.5 h-3.5 fill-rose-500" />
            <span>FINISH</span>
          </button>
        </div>
      </div>

      {/* Primary Layout Grid: Viewport + Telemetry Panel */}
      <div className="w-full flex-1 flex flex-col lg:flex-row gap-4 items-stretch justify-center">
        {/* Camera/Video Viewport Container */}
        <div
          ref={containerRef}
          className="relative flex-1 bg-black rounded-lg border border-[var(--border-subtle)] overflow-hidden flex items-center justify-center min-h-[340px] sm:min-h-[440px] lg:min-h-[540px] shadow-sm"
        >
          {/* HTML5 Video Element - active in DOM for MediaPipe and audio, kept behind canvas */}
          <video
            ref={videoRef}
            playsInline
            muted
            className="absolute inset-0 w-full h-full object-contain opacity-0 pointer-events-none -z-10"
          />

          {/* Unified CV Canvas - paints both the video frame and kinematic skeleton seamlessly */}
          <canvas
            ref={canvasRef}
            onClick={() => {
              if (videoMode === 'recorded') onTogglePlayPause();
            }}
            className={`absolute inset-0 w-full h-full object-contain ${
              videoMode === 'recorded' ? 'cursor-pointer' : ''
            }`}
          />

          {/* Loading Indicator while video pipeline warms up */}
          {!isPlaying && currentTime === 0 && !isEnded && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
              <div className="px-4 py-2 rounded bg-black/70 backdrop-blur-sm border border-slate-700/60 text-xs font-mono text-slate-300 flex items-center space-x-2 shadow-lg">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Synchronizing video pipeline...</span>
              </div>
            </div>
          )}

          {/* Corner Frame Markers */}
          <div className="absolute inset-4 sm:inset-6 pointer-events-none flex flex-col justify-between p-2">
            <div className="flex justify-between">
              <div className="w-3.5 h-3.5 border-t-2 border-l-2 border-slate-400/50" />
              <div className="w-3.5 h-3.5 border-t-2 border-r-2 border-slate-400/50" />
            </div>
            <div className="flex justify-between">
              <div className="w-3.5 h-3.5 border-b-2 border-l-2 border-slate-400/50" />
              <div className="w-3.5 h-3.5 border-b-2 border-r-2 border-slate-400/50" />
            </div>
          </div>

          {/* Fullscreen & Close Controls Top Right */}
          <div className="absolute top-3 right-3 flex items-center space-x-1.5 z-20">
            <button
              type="button"
              onClick={toggleFullscreen}
              className="p-1.5 rounded bg-black/60 backdrop-blur-sm border border-slate-700/60 text-slate-200 hover:text-white cursor-pointer"
              title="Toggle Fullscreen"
            >
              {isFullscreen ? (
                <Minimize2 className="w-3.5 h-3.5" />
              ) : (
                <Maximize2 className="w-3.5 h-3.5" />
              )}
            </button>
            <button
              type="button"
              onClick={onCloseSession}
              className="p-1.5 rounded bg-black/60 backdrop-blur-sm border border-slate-700/60 text-slate-200 hover:text-rose-400 cursor-pointer"
              title="Close Workout"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Real-time Feedback Banner */}
          {activeAlert && (
            <div className="absolute top-3 inset-x-4 sm:inset-x-12 z-20 pointer-events-none flex justify-center">
              <div
                className={`py-2 px-4 rounded border text-xs font-mono font-bold tracking-wide uppercase shadow-lg flex items-center space-x-2 ${
                  activeAlert.severity === 'critical'
                    ? 'bg-rose-950/95 border-rose-500 text-rose-200'
                    : 'bg-amber-950/95 border-amber-500 text-amber-200'
                }`}
              >
                <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                <span className="truncate">{activeAlert.message}</span>
              </div>
            </div>
          )}

          {/* Video End Completion Overlay */}
          {videoMode === 'recorded' && isEnded && (
            <div className="absolute inset-0 z-30 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
              <span className="text-xs font-mono text-emerald-400 uppercase tracking-widest font-bold mb-2">
                VIDEO COMPLETED
              </span>
              <h3 className="text-2xl font-black text-white uppercase">Analysis Finished</h3>
              <p className="text-xs text-slate-300 max-w-sm mt-2 mb-6 font-mono">
                All frames evaluated by Python FSM. Replay video or finish workout to log results.
              </p>
              <div className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={onReplay}
                  className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider rounded cursor-pointer flex items-center space-x-2"
                >
                  <Play className="w-3.5 h-3.5 fill-slate-950" />
                  <span>Replay Video</span>
                </button>
                <button
                  type="button"
                  onClick={onStopWorkout}
                  className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-white font-bold text-xs uppercase tracking-wider rounded cursor-pointer"
                >
                  View Summary
                </button>
              </div>
            </div>
          )}

          {/* Recorded Video Playback Scrubber Bar */}
          {videoMode === 'recorded' && !isEnded && (
            <div className="absolute bottom-3 inset-x-3 sm:inset-x-6 z-20 bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-lg p-2.5 flex flex-col gap-2 font-mono text-xs text-white">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-slate-300 w-10 text-right">
                  {formatTime(currentTime)}
                </span>
                <input
                  type="range"
                  min="0"
                  max={duration || 100}
                  step="0.1"
                  value={currentTime}
                  onChange={(e) => onSeek(parseFloat(e.target.value))}
                  className="flex-1 h-1 bg-slate-700 appearance-none cursor-pointer accent-emerald-500 rounded"
                />
                <span className="text-[11px] text-slate-300 w-10">{formatTime(duration)}</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={onTogglePlayPause}
                    className="p-1.5 rounded bg-emerald-500 text-slate-950 hover:bg-emerald-400 cursor-pointer"
                  >
                    {isPlaying ? (
                      <Pause className="w-3.5 h-3.5 fill-slate-950" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-slate-950" />
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={onToggleLoop}
                    className={`p-1.5 rounded border transition-colors cursor-pointer ${
                      isLooping
                        ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400'
                        : 'border-slate-700 text-slate-300'
                    }`}
                    title={isLooping ? 'Looping enabled' : 'Enable loop'}
                  >
                    <Repeat className="w-3.5 h-3.5" />
                  </button>

                  <span className="text-slate-300 truncate max-w-[120px] sm:max-w-xs text-[11px]">
                    {videoFileName || 'Recorded Workout'}
                  </span>
                </div>

                {/* Speed buttons */}
                <div className="flex items-center space-x-1 border border-slate-700 rounded p-0.5">
                  {[0.5, 0.75, 1, 1.25].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => onSpeedChange(s)}
                      className={`px-1.5 py-0.5 rounded text-[10px] cursor-pointer ${
                        playbackSpeed === s
                          ? 'bg-emerald-500 text-slate-950 font-bold'
                          : 'text-slate-300 hover:text-white'
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Technical Side Telemetry Panel */}
        <div className="w-full lg:w-80 shrink-0 flex flex-col gap-3">
          {/* Card 1: Repetition / Duration Primary Metric */}
          <div className="p-5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] flex flex-col justify-between shadow-sm">
            <div className="flex items-center justify-between text-xs font-mono uppercase text-[var(--text-secondary)] mb-1">
              <span>{isDuration ? 'HOLD DURATION' : 'REPETITIONS'}</span>
              <span className="text-emerald-500 font-bold">
                {isDuration
                  ? `TARGET: ${exercise.targetDuration || 30}s`
                  : `GOAL: ${exercise.defaultReps}`}
              </span>
            </div>

            <div className="flex items-baseline space-x-3 my-2">
              <span
                className={`text-6xl sm:text-7xl font-black font-mono tracking-tight text-[var(--text-primary)] ${
                  repBumpAnimation ? 'stat-bump text-emerald-500' : ''
                }`}
              >
                {isDuration
                  ? `${Math.floor(exerciseResult?.current_duration ?? 0)}s`
                  : exerciseResult?.counter ?? 0}
              </span>
              <span className="text-xs font-mono text-[var(--text-muted)] uppercase">
                {isDuration ? 'SECONDS' : 'REPS'}
              </span>
            </div>

            {/* Current FSM State */}
            <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between font-mono text-xs">
              <span className="text-[var(--text-muted)] uppercase">FSM STATE</span>
              <span className="px-2.5 py-0.5 rounded bg-[var(--bg-card-hover)] border border-[var(--border-strong)] text-emerald-500 font-bold uppercase">
                {exerciseResult?.current_state || 'READY'}
              </span>
            </div>
          </div>

          {/* Card 2: Biomechanic Form Score */}
          <div className="p-5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] flex items-center justify-between font-mono shadow-sm">
            <div>
              <span className="text-xs text-[var(--text-secondary)] uppercase block mb-1">FORM SCORE</span>
              <div className="flex items-baseline space-x-1.5">
                <span className="text-3xl font-black text-[var(--text-primary)]">{currentScore}</span>
                <span className="text-xs text-[var(--text-muted)]">/ 100</span>
              </div>
              <span className="text-[11px] font-bold text-emerald-500 mt-1 block">
                {scoreLabel}
              </span>
            </div>

            <div className="w-14 h-14 rounded-lg border border-[var(--border-strong)] bg-[var(--bg-card-solid)] flex flex-col items-center justify-center shadow-inner">
              <span className="text-2xl font-black text-[var(--text-primary)]">
                {exerciseResult?.form_grade || 'A'}
              </span>
              <span className="text-[8px] text-[var(--text-muted)] uppercase font-bold">GRADE</span>
            </div>
          </div>

          {/* Card 3: Bilateral Limb Breakdown */}
          {exercise.bilateral && (
            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] text-center shadow-sm">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">LEFT LIMB</span>
                <span className="text-xl font-bold text-[var(--text-primary)]">
                  {exerciseResult?.counter_left ?? 0}
                </span>
              </div>
              <div className="p-3 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] text-center shadow-sm">
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">RIGHT LIMB</span>
                <span className="text-xl font-bold text-[var(--text-primary)]">
                  {exerciseResult?.counter_right ?? 0}
                </span>
              </div>
            </div>
          )}

          {/* Guide Drawer */}
          {showGuide && (
            <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] text-xs font-mono text-[var(--text-secondary)] shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[var(--text-primary)] font-bold uppercase">TECHNIQUE SPEC</span>
                <span className="text-emerald-500 font-semibold">{exercise.difficulty}</span>
              </div>
              <p className="text-[var(--text-secondary)] leading-normal mb-3">{exercise.description}</p>
              <div className="flex flex-wrap gap-1">
                {exercise.targetMuscles.map((m) => (
                  <span
                    key={m}
                    className="px-2 py-0.5 rounded bg-[var(--bg-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] text-[10px]"
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
