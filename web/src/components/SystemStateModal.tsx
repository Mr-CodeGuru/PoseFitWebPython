import React from 'react';
import { AlertCircle, Camera, RotateCcw, ShieldAlert, Cpu } from 'lucide-react';

export type SystemStateType =
  | 'engine_loading'
  | 'camera_loading'
  | 'camera_denied'
  | 'camera_unavailable'
  | 'pose_loading'
  | 'pose_not_detected'
  | 'error';

interface SystemStateModalProps {
  state: SystemStateType;
  customMessage?: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const SystemStateModal: React.FC<SystemStateModalProps> = ({
  state,
  customMessage,
  onRetry,
  onDismiss,
}) => {
  const getContent = () => {
    switch (state) {
      case 'camera_denied':
        return {
          icon: <ShieldAlert className="w-8 h-8 text-rose-500" />,
          title: 'Camera Permission Denied',
          description:
            'Browser camera permissions are required for real-time computer vision tracking. Click the camera or lock icon in your browser address bar and select "Allow" for this site, then refresh.',
          actionLabel: 'Retry Permission',
        };
      case 'camera_unavailable':
        return {
          icon: <Camera className="w-8 h-8 text-amber-500" />,
          title: 'Camera Device Not Found',
          description:
            'No webcam video feed could be opened. Verify that no other application (Zoom, FaceTime, Teams) is currently locking the video device.',
          actionLabel: 'Check Device',
        };
      case 'camera_loading':
        return {
          icon: <Camera className="w-8 h-8 text-emerald-500 animate-pulse" />,
          title: 'Initializing Video Stream',
          description: 'Requesting hardware video access and matching sensor aspect ratio...',
          actionLabel: null,
        };
      case 'engine_loading':
        return {
          icon: <Cpu className="w-8 h-8 text-emerald-500 animate-pulse" />,
          title: 'Initializing Kinematics Core',
          description: 'Loading compiled Python CV kinematics engine and validating state tables...',
          actionLabel: null,
        };
      case 'pose_loading':
        return {
          icon: <Cpu className="w-8 h-8 text-emerald-500 animate-pulse" />,
          title: 'Loading Pose Estimation Model',
          description: 'Caching MediaPipe 33-landmark neural network weights locally...',
          actionLabel: null,
        };
      case 'error':
      default:
        return {
          icon: <AlertCircle className="w-8 h-8 text-rose-500" />,
          title: 'Tracking System Error',
          description: customMessage || 'An unexpected error occurred during processing.',
          actionLabel: 'Retry',
        };
    }
  };

  const content = getContent();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm">
      <div className="w-full max-w-md bg-[var(--bg-card-solid)] border border-[var(--border-subtle)] rounded p-6 shadow-2xl text-center">
        <div className="flex justify-center mb-4">{content.icon}</div>
        <h3 className="text-lg font-black text-[var(--text-primary)] uppercase tracking-tight">
          {content.title}
        </h3>
        <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed font-mono">
          {content.description}
        </p>

        <div className="mt-6 flex items-center justify-center gap-3">
          {content.actionLabel && onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider rounded cursor-pointer flex items-center space-x-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{content.actionLabel}</span>
            </button>
          )}

          {onDismiss && (
            <button
              type="button"
              onClick={onDismiss}
              className="px-5 py-2.5 bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-bold text-xs uppercase tracking-wider rounded cursor-pointer"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
