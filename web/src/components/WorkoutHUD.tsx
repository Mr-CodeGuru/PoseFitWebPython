import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { ExerciseResult, WorkoutSummary } from '../types/posefit';
import { EXERCISE_CATALOG, EXERCISE_MAP, type ExerciseDefinition } from '../data/exercises';
import { BrowserPoseDetector, type PoseFrameData } from '../cv/poseDetector';
import { SkeletonRenderer } from '../cv/skeletonRenderer';
import { posefitClient } from '../client/posefitClient';
import { audioFeedback } from '../utils/audioFeedback';

// Discrete Views
import { LandingView } from './LandingView';
import { ChooseExerciseView } from './ChooseExerciseView';
import { WorkoutSetupView } from './WorkoutSetupView';
import { LiveWorkoutView } from './LiveWorkoutView';
import { ResultsView } from './ResultsView';
import { SystemStateModal, type SystemStateType } from './SystemStateModal';
import { ThemeToggle } from './ThemeToggle';
import { Footer } from './Footer';

type AppStep = 'landing' | 'choose_exercise' | 'setup' | 'live' | 'results';

export const WorkoutHUD: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>('landing');
  const [selectedExerciseId, setSelectedExerciseId] = useState<string>('squat');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const poseDetectorRef = useRef<BrowserPoseDetector | null>(null);

  const [isEngineReady, setIsEngineReady] = useState(false);
  const [systemModal, setSystemModal] = useState<{
    state: SystemStateType;
    message?: string;
  } | null>(null);

  // Runtime Tracking State
  const [exerciseResult, setExerciseResult] = useState<ExerciseResult | null>(null);
  const [workoutSummary, setWorkoutSummary] = useState<WorkoutSummary | null>(null);
  const [videoMode, setVideoMode] = useState<'camera' | 'recorded'>('camera');
  const [videoFileName, setVideoFileName] = useState<string | null>(null);
  const [uploadedVideoFile, setUploadedVideoFile] = useState<File | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLooping, setIsLooping] = useState(false);
  const [isEnded, setIsEnded] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const [isMirrored, setIsMirrored] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [, setLastCompletedRep] = useState<number>(0);
  const lastCompletedRepRef = useRef<number>(0);
  const exerciseResultRef = useRef<ExerciseResult | null>(null);
  exerciseResultRef.current = exerciseResult;
  const isMirroredRef = useRef<boolean>(isMirrored);
  isMirroredRef.current = isMirrored;
  const [repBumpAnimation, setRepBumpAnimation] = useState(false);
  const [activeAlert, setActiveAlert] = useState<{ message: string; severity: string } | null>(null);

  const lastAlertTimeRef = useRef<number>(0);
  const lastAlertMsgRef = useRef<string>('');

  const selectedExercise: ExerciseDefinition =
    EXERCISE_MAP[selectedExerciseId] || EXERCISE_CATALOG[0];

  // Initialize PoseFit Engine & Subscribe to server results
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        await posefitClient.init();
        if (mounted) {
          posefitClient.startExercise(selectedExerciseId);
          setIsEngineReady(true);
        }
      } catch (err: unknown) {
        console.error('Failed to initialize PoseFit engine:', err);
        if (mounted) {
          setSystemModal({
            state: 'engine_loading',
            message: 'Failed to connect to local PoseFit Python backend.',
          });
        }
      }
    })();

    const unsubscribe = posefitClient.subscribe((result) => {
      if (!mounted) return;
      setExerciseResult(result);

      // Rep completion detection & celebration (using ref to avoid effect restart)
      if (result.rep_completed && result.counter > lastCompletedRepRef.current) {
        lastCompletedRepRef.current = result.counter;
        setLastCompletedRep(result.counter);
        setRepBumpAnimation(true);
        setTimeout(() => setRepBumpAnimation(false), 300);
        audioFeedback.playRepCompleteSound();
      }

      // Feedback alert banner with rate limiting
      if (result.feedback_alerts && result.feedback_alerts.length > 0) {
        const topAlert = result.feedback_alerts[0];
        setActiveAlert({
          message: topAlert.message,
          severity: topAlert.severity,
        });

        const now = Date.now();
        if (
          (topAlert.severity === 'warning' || topAlert.severity === 'critical') &&
          (topAlert.message !== lastAlertMsgRef.current || now - lastAlertTimeRef.current > 3500)
        ) {
          lastAlertTimeRef.current = now;
          lastAlertMsgRef.current = topAlert.message;
          audioFeedback.playWarningAlertSound();
        }
      } else {
        setActiveAlert(null);
        lastAlertMsgRef.current = '';
      }
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [selectedExerciseId]);

  // Frame processing callback: streams landmarks to Python and renders video+skeleton
  const handlePoseFrame = useCallback(
    (data: PoseFrameData) => {
      if (!isEngineReady) return;

      try {
        // Stream binary landmarks to Python backend (results delivered asynchronously via subscribe)
        posefitClient.processLandmarksFlat(
          data.flatLandmarks,
          data.width,
          data.height,
          data.timestampSec
        );

        // Draw video frame, skeleton overlay, and angle badges on the canvas
        const canvas = canvasRef.current;
        const video = videoRef.current;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          if (ctx) {
            if (canvas.width !== data.width || canvas.height !== data.height) {
              canvas.width = data.width;
              canvas.height = data.height;
            }
            SkeletonRenderer.draw(
              ctx,
              video,
              data.rawLandmarks,
              data.width,
              data.height,
              exerciseResultRef.current,
              isMirroredRef.current
            );
          }
        }
      } catch (err) {
        console.warn('[Frame] Evaluation exception:', err);
      }
    },
    [isEngineReady]
  );

  // Stable reference so frame callbacks don't invalidate useEffect dependencies
  const handlePoseFrameRef = useRef<(data: PoseFrameData) => void>(handlePoseFrame);
  handlePoseFrameRef.current = handlePoseFrame;

  // Close active workout session helper
  const handleCloseSession = useCallback(() => {
    if (poseDetectorRef.current) {
      poseDetectorRef.current.stop();
      poseDetectorRef.current = null;
    }
    const video = videoRef.current;
    if (video) {
      video.pause();
      video.srcObject = null;
    }
    setIsPlaying(false);
  }, []);

  // Listen to video element time updates, duration, play/pause, and end
  useEffect(() => {
    const video = videoRef.current;
    if (!video || currentStep !== 'live') return;

    const onTime = () => setCurrentTime(video.currentTime);
    const onMeta = () => setDuration(video.duration || 0);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onEnd = () => {
      if (isLooping) {
        video.currentTime = 0;
        video.play().catch(console.error);
      } else {
        setIsPlaying(false);
        setIsEnded(true);
      }
    };

    video.addEventListener('timeupdate', onTime);
    video.addEventListener('loadedmetadata', onMeta);
    video.addEventListener('durationchange', onMeta);
    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    video.addEventListener('ended', onEnd);

    const onSeeked = () => {
      if (video.paused && poseDetectorRef.current) {
        poseDetectorRef.current.processCurrentFrame(video);
      }
    };
    video.addEventListener('seeked', onSeeked);

    return () => {
      video.removeEventListener('timeupdate', onTime);
      video.removeEventListener('loadedmetadata', onMeta);
      video.removeEventListener('durationchange', onMeta);
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      video.removeEventListener('ended', onEnd);
      video.removeEventListener('seeked', onSeeked);
    };
  }, [currentStep, isLooping]);

  // Start pose detector and video source when entering live step
  useEffect(() => {
    if (currentStep !== 'live') {
      handleCloseSession();
      return;
    }

    const video = videoRef.current;
    if (!video) return;

    let isCancelled = false;
    const detector = new BrowserPoseDetector();
    poseDetectorRef.current = detector;

    detector
      .initialize((data: PoseFrameData) => {
        if (!isCancelled && handlePoseFrameRef.current) {
          handlePoseFrameRef.current(data);
        }
      })
      .then(async () => {
        if (isCancelled || !videoRef.current) return;

        if (videoMode === 'camera') {
          setIsMirrored(true);
          await detector.startCamera(videoRef.current);
          if (!isCancelled) setIsPlaying(true);
        } else if (videoMode === 'recorded' && uploadedVideoFile) {
          setIsMirrored(false);
          await detector.startVideo(videoRef.current, uploadedVideoFile, isLooping);
          if (!isCancelled) setIsPlaying(true);
        }
      })
      .catch((err: unknown) => {
        if (isCancelled) return;
        console.error('Pose detector init error:', err);
        setSystemModal({
          state: 'camera_denied',
          message:
            videoMode === 'camera'
              ? 'Camera access was denied or is unavailable. Please check permissions.'
              : 'Failed to load video file. Please check format.',
        });
      });

    return () => {
      isCancelled = true;
      detector.stop();
    };
  }, [currentStep, videoMode, uploadedVideoFile, handleCloseSession]);

  // Video controls
  const handleTogglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().catch(console.error);
    } else {
      video.pause();
    }
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = time;
    setCurrentTime(time);
    if (isEnded && time < (video.duration || 0)) {
      setIsEnded(false);
    }
  };

  const handleToggleMute = () => {
    setIsMuted((prev) => {
      const next = !prev;
      if (videoRef.current) {
        videoRef.current.muted = next;
      }
      return next;
    });
  };

  const handleToggleLoop = () => {
    setIsLooping((prev) => {
      const next = !prev;
      if (videoRef.current) {
        videoRef.current.loop = next;
      }
      return next;
    });
  };

  const handleToggleMirror = () => {
    setIsMirrored((prev) => !prev);
  };

  const handleSpeedChange = (speed: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
    setPlaybackSpeed(speed);
  };

  const handleReplay = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    video.play().catch(console.error);
    setIsPlaying(true);
    setIsEnded(false);
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
  };

  const handleResetCounter = () => {
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
  };

  const handleCloseToChoose = () => {
    handleCloseSession();
    setCurrentStep('choose_exercise');
  };

  const handleFileUpload = (file: File) => {
    handleCloseSession();
    setUploadedVideoFile(file);
    setVideoMode('recorded');
    setVideoFileName(file.name);
    setIsEnded(false);
    setCurrentTime(0);
    setIsMirrored(false);
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
    setCurrentStep('live');
  };

  const handleStartCameraSetup = () => {
    handleCloseSession();
    setUploadedVideoFile(null);
    setVideoMode('camera');
    setVideoFileName(null);
    setIsEnded(false);
    setCurrentTime(0);
    setIsMirrored(true);
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
    setCurrentStep('live');
  };

  const handleLoadSample = () => {
    handleStartCameraSetup();
  };

  // Navigation handlers
  const handleStartWorkout = () => {
    setCurrentStep('choose_exercise');
  };

  const handleSelectExercise = (id: string) => {
    setSelectedExerciseId(id);
    posefitClient.startExercise(id);
    setCurrentStep('setup');
  };

  const handleStopWorkout = () => {
    setIsPlaying(false);
    if (videoRef.current) {
      videoRef.current.pause();
    }
    try {
      const summary = posefitClient.stopExercise();
      setWorkoutSummary(summary);
      setCurrentStep('results');
    } catch (err) {
      console.error('Failed to stop workout:', err);
    }
  };

  const handleRestartWorkout = () => {
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
    setExerciseResult(null);
    setWorkoutSummary(null);
    setCurrentStep('live');
  };

  const handleChooseAnother = () => {
    posefitClient.resetCurrentExercise();
    lastCompletedRepRef.current = 0;
    setLastCompletedRep(0);
    setExerciseResult(null);
    setWorkoutSummary(null);
    setCurrentStep('choose_exercise');
  };

  const handleBackToLanding = () => {
    handleCloseSession();
    setExerciseResult(null);
    setWorkoutSummary(null);
    setCurrentStep('landing');
  };

  return (
    <div className="flex flex-col min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] font-sans selection:bg-emerald-500 selection:text-white transition-colors duration-200">
      {/* Global Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-[var(--border-subtle)] bg-[var(--bg-header)] backdrop-blur-md transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={handleBackToLanding}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <span className="text-xl font-black text-white tracking-wider">PF</span>
            </div>
            <div>
              <span className="text-lg font-bold text-[var(--text-primary)]">
                PoseFit
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                AI Coach
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {currentStep !== 'landing' && (
              <button
                onClick={handleChooseAnother}
                className="text-xs sm:text-sm font-medium px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
              >
                Change Exercise
              </button>
            )}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Flow Content */}
      <main className="flex-1 flex flex-col">
        {currentStep === 'landing' && (
          <LandingView
            exercises={EXERCISE_CATALOG}
            onStart={handleStartWorkout}
            onSelectExercise={handleSelectExercise}
            isEngineReady={isEngineReady}
          />
        )}

        {currentStep === 'choose_exercise' && (
          <ChooseExerciseView
            exercises={EXERCISE_CATALOG}
            selectedExerciseId={selectedExerciseId}
            onSelect={(id: string) => setSelectedExerciseId(id)}
            onConfirm={() => setCurrentStep('setup')}
            onBack={handleBackToLanding}
          />
        )}

        {currentStep === 'setup' && (
          <WorkoutSetupView
            exercise={selectedExercise}
            onStartCamera={handleStartCameraSetup}
            onFileUpload={handleFileUpload}
            onLoadSample={handleLoadSample}
            onBack={() => setCurrentStep('choose_exercise')}
            isEngineReady={isEngineReady}
          />
        )}

        {currentStep === 'live' && (
          <LiveWorkoutView
            exercise={selectedExercise}
            videoRef={videoRef}
            canvasRef={canvasRef}
            exerciseResult={exerciseResult}
            videoMode={videoMode}
            videoFileName={videoFileName}
            isPlaying={isPlaying}
            isLooping={isLooping}
            isEnded={isEnded}
            currentTime={currentTime}
            duration={duration}
            isMuted={isMuted}
            isMirrored={isMirrored}
            playbackSpeed={playbackSpeed}
            repBumpAnimation={repBumpAnimation}
            activeAlert={activeAlert}
            onTogglePlayPause={handleTogglePlay}
            onToggleLoop={handleToggleLoop}
            onReplay={handleReplay}
            onSeek={handleSeek}
            onSpeedChange={handleSpeedChange}
            onToggleMirror={handleToggleMirror}
            onToggleMute={handleToggleMute}
            onResetCounter={handleResetCounter}
            onStopWorkout={handleStopWorkout}
            onCloseSession={handleCloseToChoose}
          />
        )}

        {currentStep === 'results' && workoutSummary && (
          <ResultsView
            summary={workoutSummary}
            onWorkoutAgain={handleRestartWorkout}
            onChooseAnother={handleChooseAnother}
          />
        )}
      </main>

      {/* Global Footer */}
      <Footer />

      {/* System State & Permission Modal */}
      {systemModal && (
        <SystemStateModal
          state={systemModal.state}
          customMessage={systemModal.message}
          onDismiss={() => setSystemModal(null)}
        />
      )}
    </div>
  );
};
