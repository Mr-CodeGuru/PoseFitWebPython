export interface PoseFrameData {
  flatLandmarks: Float32Array;
  rawLandmarks: any;
  width: number;
  height: number;
  timestampSec: number;
}

export type PoseFrameCallback = (data: PoseFrameData) => void;

export class BrowserPoseDetector {
  private pose: any = null;
  private isRunning: boolean = false;
  private isProcessing: boolean = false;
  private onFrameCallback: PoseFrameCallback | null = null;
  private animFrameId: number | null = null;
  private videoFrameCallbackId: number | null = null;
  private activeStream: MediaStream | null = null;
  private currentVideoElement: HTMLVideoElement | null = null;

  private async loadScript(src: string): Promise<boolean> {
    return new Promise((resolve) => {
      const existing = document.querySelector(`script[src="${src}"]`);
      if (existing) {
        resolve(true);
        return;
      }
      const script = document.createElement('script');
      script.src = src;
      script.crossOrigin = 'anonymous';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.head.appendChild(script);
    });
  }

  private async ensureMediaPipeLoaded(): Promise<void> {
    if (typeof window !== 'undefined' && (window as any).Pose) {
      return;
    }

    // Try local asset first
    const localLoaded = await this.loadScript('/mediapipe/pose/pose.js');
    if (localLoaded && (window as any).Pose) return;

    // Fallback to CDN
    const cdnLoaded = await this.loadScript(
      'https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.5.1675469404/pose.js'
    );
    if (cdnLoaded && (window as any).Pose) return;

    // Wait a brief moment if script is currently initializing
    const start = Date.now();
    while (Date.now() - start < 3000) {
      if ((window as any).Pose) return;
      await new Promise((r) => setTimeout(r, 50));
    }

    throw new Error(
      'Failed to load MediaPipe Pose engine. Check network or ad-blocker settings.'
    );
  }

  public async initialize(onFrame: PoseFrameCallback): Promise<void> {
    this.onFrameCallback = onFrame;
    await this.ensureMediaPipeLoaded();

    const PoseClass = (window as any).Pose;
    this.pose = new PoseClass({
      locateFile: (file: string) => {
        // Try local static files first, fallback to CDN
        return `/mediapipe/pose/${file}`;
      },
    });

    this.pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      enableSegmentation: false,
      smoothSegmentation: false,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    this.pose.onResults((results: any) => {
      this.isProcessing = false;
      if (!this.isRunning || !this.onFrameCallback) return;

      const landmarks = results.poseLandmarks;
      if (!landmarks || landmarks.length < 33) return;

      const flatData = new Float32Array(33 * 4);
      for (let i = 0; i < 33; i++) {
        const lm = landmarks[i];
        const offset = i * 4;
        flatData[offset] = lm.x;
        flatData[offset + 1] = lm.y;
        flatData[offset + 2] = lm.z ?? 0.0;
        flatData[offset + 3] = lm.visibility ?? 1.0;
      }

      const width = this.currentVideoElement?.videoWidth || results.image?.width || 1280;
      const height = this.currentVideoElement?.videoHeight || results.image?.height || 720;
      const timestampSec = performance.now() / 1000.0;

      try {
        this.onFrameCallback({
          flatLandmarks: flatData,
          rawLandmarks: landmarks,
          width,
          height,
          timestampSec,
        });
      } catch (err) {
        console.warn('[PoseDetector] Error in frame callback:', err);
      }
    });

    await this.pose.initialize();
  }

  /**
   * Starts processing from real webcam stream
   */
  public async startCamera(videoElement: HTMLVideoElement): Promise<void> {
    if (!this.pose) throw new Error('Pose detector not initialized');

    this.stop(); // Stop any previous session
    this.currentVideoElement = videoElement;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error(
        'Your browser does not support webcam access or is not running in a secure (HTTPS/localhost) context.'
      );
    }

    try {
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280, max: 1920 },
            height: { ideal: 720, max: 1080 },
          },
          audio: false,
        });
      } catch (_err) {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      this.activeStream = stream;
      videoElement.srcObject = stream;
      videoElement.muted = true;
      videoElement.playsInline = true;

      await videoElement.play();
      this.isRunning = true;
      this.runDetectionLoop(videoElement);
    } catch (err: any) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        throw new Error(
          'Camera permission was denied. Please click the camera/lock icon in your browser address bar and choose "Allow".'
        );
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        throw new Error('No webcam device was found on this computer/device.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        throw new Error(
          'Your webcam is currently being used by another application (e.g. Zoom, FaceTime, Teams). Please close other apps and retry.'
        );
      } else {
        throw new Error(`Webcam error: ${err.message || err.name || 'Unknown error'}`);
      }
    }
  }

  /**
   * Starts processing from a pre-recorded video source (file or URL)
   */
  private currentBlobUrl: string | null = null;

  public async startVideo(
    videoElement: HTMLVideoElement,
    source: File | string,
    loop: boolean = false
  ): Promise<void> {
    if (!this.pose) throw new Error('Pose detector not initialized');

    this.stop(); // Stop any previous session
    this.currentVideoElement = videoElement;

    videoElement.srcObject = null;
    if (this.currentBlobUrl) {
      try {
        URL.revokeObjectURL(this.currentBlobUrl);
      } catch (_) {}
      this.currentBlobUrl = null;
    }

    if (typeof source === 'string') {
      videoElement.src = source;
    } else {
      this.currentBlobUrl = URL.createObjectURL(source);
      videoElement.src = this.currentBlobUrl;
    }

    videoElement.muted = true;
    videoElement.playsInline = true;
    videoElement.loop = loop;
    videoElement.currentTime = 0;
    videoElement.load();

    if (videoElement.readyState < 2) {
      await new Promise<void>((resolve, reject) => {
        let isDone = false;
        const done = () => {
          if (!isDone) {
            isDone = true;
            cleanup();
            resolve();
          }
        };
        const onErr = () => {
          if (!isDone) {
            isDone = true;
            cleanup();
            reject(new Error('Failed to load video file'));
          }
        };
        const cleanup = () => {
          videoElement.removeEventListener('loadeddata', done);
          videoElement.removeEventListener('canplay', done);
          videoElement.removeEventListener('error', onErr);
        };
        videoElement.addEventListener('loadeddata', done);
        videoElement.addEventListener('canplay', done);
        videoElement.addEventListener('error', onErr);
      });
    }

    try {
      await videoElement.play();
    } catch (err) {
      console.warn('[PoseDetector] Autoplay prevented, awaiting user gesture', err);
    }

    this.isRunning = true;
    this.runDetectionLoop(videoElement);
  }

  public async processCurrentFrame(videoElement: HTMLVideoElement): Promise<void> {
    if (!this.pose || this.isProcessing) return;
    if (videoElement.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;

    this.isProcessing = true;
    try {
      await this.pose.send({ image: videoElement });
    } catch (err) {
      this.isProcessing = false;
      console.warn('[PoseDetector] Manual frame evaluation failed:', err);
    }
  }

  private runDetectionLoop(videoElement: HTMLVideoElement): void {
    const loop = async () => {
      if (!this.isRunning || !this.pose) return;

      if (
        !this.isProcessing &&
        !videoElement.paused &&
        !videoElement.ended &&
        videoElement.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA
      ) {
        this.isProcessing = true;
        try {
          await this.pose.send({ image: videoElement });
        } catch (err) {
          this.isProcessing = false;
          console.warn('[PoseDetector] Frame dropped or send failed:', err);
        }
      }

      if (this.isRunning) {
        if ('requestVideoFrameCallback' in videoElement) {
          this.videoFrameCallbackId = (videoElement as any).requestVideoFrameCallback(loop);
        } else {
          this.animFrameId = requestAnimationFrame(loop);
        }
      }
    };

    loop();
  }

  public stop(): void {
    this.isRunning = false;
    this.isProcessing = false;

    if (
      this.currentVideoElement &&
      this.videoFrameCallbackId !== null &&
      'cancelVideoFrameCallback' in this.currentVideoElement
    ) {
      try {
        (this.currentVideoElement as any).cancelVideoFrameCallback(this.videoFrameCallbackId);
      } catch (_) {}
      this.videoFrameCallbackId = null;
    }

    if (this.animFrameId !== null) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }

    if (this.activeStream) {
      this.activeStream.getTracks().forEach((track) => track.stop());
      this.activeStream = null;
    }
  }
}
