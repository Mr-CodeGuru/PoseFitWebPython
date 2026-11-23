import React, { useRef } from 'react';
import { ArrowLeft, Camera, Upload, FileVideo, CheckCircle2 } from 'lucide-react';
import type { ExerciseDefinition } from '../data/exercises';

interface WorkoutSetupViewProps {
  exercise: ExerciseDefinition;
  onStartCamera: () => void;
  onFileUpload: (file: File) => void;
  onLoadSample: () => void;
  onBack: () => void;
  isEngineReady: boolean;
}

export const WorkoutSetupView: React.FC<WorkoutSetupViewProps> = ({
  exercise,
  onStartCamera,
  onFileUpload,
  onLoadSample,
  onBack,
  isEngineReady,
}) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8">
      {/* Header Bar */}
      <div className="flex items-center justify-between pb-6 border-b border-[var(--border-subtle)]">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>CHANGE EXERCISE</span>
        </button>

        <span className="text-xs font-mono text-[var(--text-muted)]">STEP 2 OF 3</span>
      </div>

      <div className="mt-8 text-center max-w-xl mx-auto">
        <span className="text-xs font-mono uppercase tracking-widest text-emerald-500 font-bold block mb-1">
          {exercise.name} Setup
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-[var(--text-primary)] tracking-tight">
          Select Tracking Source
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-2 leading-relaxed">
          Position your camera so your full body is visible within the frame. Ensure good ambient lighting without strong backlighting.
        </p>
      </div>

      {/* Source Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 max-w-2xl mx-auto">
        {/* Live Camera Option */}
        <div
          onClick={isEngineReady ? onStartCamera : undefined}
          className={`p-6 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-emerald-500/80 hover:bg-[var(--bg-card-hover)] transition-all flex flex-col justify-between text-left group cursor-pointer shadow-sm ${
            !isEngineReady ? 'opacity-50 pointer-events-none' : ''
          }`}
        >
          <div>
            <div className="w-10 h-10 rounded border border-[var(--border-strong)] bg-[var(--bg-card-solid)] text-emerald-500 flex items-center justify-center mb-4 group-hover:border-emerald-500 transition-colors">
              <Camera className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-[var(--text-primary)] group-hover:text-emerald-500 transition-colors">
              Live Webcam
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
              Real-time pose tracking with instant acoustic and visual form correction.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
            <span>RECOMMENDED</span>
            <span className="text-emerald-500 font-bold group-hover:translate-x-1 transition-transform">
              CONNECT →
            </span>
          </div>
        </div>

        {/* Video Upload Option */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`p-6 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-card-hover)] transition-all flex flex-col justify-between text-left group cursor-pointer shadow-sm ${
            !isEngineReady ? 'opacity-50 pointer-events-none' : ''
          }`}
        >
          <div>
            <div className="w-10 h-10 rounded border border-[var(--border-strong)] bg-[var(--bg-card-solid)] text-sky-500 flex items-center justify-center mb-4 group-hover:border-slate-400 transition-colors">
              <Upload className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-[var(--text-primary)] group-hover:text-sky-500 transition-colors">
              Pre-recorded Video
            </h3>
            <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
              Upload MP4/WebM video of yourself performing the movement for post-hoc kinematic form analysis.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
            <span>FILE UPLOAD</span>
            <span className="text-sky-500 font-bold group-hover:translate-x-1 transition-transform">
              SELECT →
            </span>
          </div>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/mp4,video/webm,video/quicktime,video/x-m4v"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Sample Video Fallback */}
      <div className="mt-6 text-center">
        <button
          type="button"
          onClick={onLoadSample}
          disabled={!isEngineReady}
          className="inline-flex items-center space-x-1.5 text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer disabled:opacity-50"
        >
          <FileVideo className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <span>Or test immediately with a recorded demo video</span>
        </button>
      </div>

      {/* Camera Framing Checklist */}
      <div className="mt-12 max-w-2xl mx-auto p-4 rounded border border-[var(--border-subtle)] bg-[var(--bg-card)] text-left shadow-sm">
        <span className="text-xs font-mono text-[var(--text-secondary)] uppercase font-bold tracking-wider block mb-2">
          Positioning Checklist
        </span>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[var(--text-secondary)]">
          <li className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>Head to ankles visible in frame</span>
          </li>
          <li className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>Even ambient room lighting</span>
          </li>
          <li className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>Camera steady at hip height</span>
          </li>
          <li className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>Fitted athletic clothing</span>
          </li>
        </ul>
      </div>
    </div>
  );
};
