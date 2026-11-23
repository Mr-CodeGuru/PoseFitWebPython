import type { ExerciseResult, WorkoutSummary } from '../types/posefit';

export interface PoseClientOptions {
  wsUrl?: string;
  reconnectIntervalMs?: number;
  maxReconnectIntervalMs?: number;
}

export type ResultCallback = (result: ExerciseResult) => void;

/**
 * PoseClient: WebSocket transport layer for PoseFit kinematics streaming.
 *
 * Implements Mode A (Browser landmarks -> Python analytics) with:
 * - Persistent WebSocket connection to /ws/pose
 * - Automatic exponential backoff reconnection
 * - Flat Float32Array binary landmark streaming (528 bytes/frame)
 * - High-performance streaming interface
 */
export class PoseClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectIntervalMs: number;
  private maxReconnectIntervalMs: number;
  private currentRetryDelay: number;
  private currentExercise: string = 'squat';
  private isInitialized: boolean = false;
  private initPromise: Promise<void> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private listeners: Set<ResultCallback> = new Set();
  private lastResult: ExerciseResult;
  private lastSummary: WorkoutSummary | null = null;
  private pendingQueue: (string | ArrayBufferView)[] = [];

  constructor(options: PoseClientOptions = {}) {
    this.reconnectIntervalMs = options.reconnectIntervalMs ?? 500;
    this.maxReconnectIntervalMs = options.maxReconnectIntervalMs ?? 5000;
    this.currentRetryDelay = this.reconnectIntervalMs;

    if (options.wsUrl) {
      this.url = options.wsUrl;
    } else if (typeof window !== 'undefined') {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      this.url = `${proto}//${window.location.host}/ws/pose`;
    } else {
      this.url = 'ws://127.0.0.1:8000/ws/pose';
    }

    this.lastResult = {
      exercise_name: this.currentExercise,
      counter: 0,
      counter_left: 0,
      counter_right: 0,
      current_state: 'start',
      prev_state: null,
      state_left: null,
      state_right: null,
      current_duration: 0.0,
      target_duration: null,
      is_holding: false,
      angles: {},
      form_score: 100.0,
      avg_form_score: 100.0,
      form_grade: 'A',
      feedback_alerts: [],
      rep_completed: false,
    };
  }

  public async init(): Promise<void> {
    if (this.isInitialized && this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }
    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = new Promise<void>((resolve, reject) => {
      this.connect(resolve, reject);
    });

    return this.initPromise;
  }

  private connect(resolve?: () => void, reject?: (err: unknown) => void): void {
    try {
      const targetUrl = `${this.url}?exercise=${encodeURIComponent(this.currentExercise)}`;
      this.ws = new WebSocket(targetUrl);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        this.isInitialized = true;
        this.currentRetryDelay = this.reconnectIntervalMs;

        // Flush any queued start/frame payloads
        while (this.pendingQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
          const item = this.pendingQueue.shift();
          if (item) (this.ws as any).send(item);
        }

        if (resolve) resolve();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          if (typeof event.data === 'string') {
            const parsed = JSON.parse(event.data);
            if (parsed.status === 'stopped' && parsed.summary) {
              this.lastSummary = parsed.summary as WorkoutSummary;
            } else if (parsed.exercise_name !== undefined) {
              const newResult = parsed as ExerciseResult;
              // Strictly non-decreasing counter during active exercise session
              if (newResult.exercise_name === this.currentExercise) {
                newResult.counter = Math.max(this.lastResult.counter, newResult.counter);
                newResult.counter_left = Math.max(this.lastResult.counter_left, newResult.counter_left);
                newResult.counter_right = Math.max(this.lastResult.counter_right, newResult.counter_right);
              }
              this.lastResult = newResult;
              this.notifyListeners(this.lastResult);
            }
          }
        } catch (err) {
          console.warn('[PoseClient] Failed to deserialize WebSocket message:', err);
        }
      };

      this.ws.onerror = (err: Event) => {
        if (!this.isInitialized && reject) {
          reject(err);
        }
      };

      this.ws.onclose = () => {
        this.scheduleReconnect();
      };
    } catch (err) {
      if (!this.isInitialized && reject) {
        reject(err);
      }
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.currentRetryDelay = Math.min(
        this.currentRetryDelay * 1.5,
        this.maxReconnectIntervalMs
      );
      this.connect();
    }, this.currentRetryDelay);
  }

  public subscribe(callback: ResultCallback): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners(res: ExerciseResult): void {
    for (const listener of this.listeners) {
      try {
        listener(res);
      } catch (err) {
        console.error('[PoseClient] Listener threw exception:', err);
      }
    }
  }

  public getAvailableExercises(): string[] {
    return [
      'squat',
      'push_up',
      'plank',
      'hammer_curl',
      'bicep_curl',
      'jumping_jack',
      'lunge',
      'shoulder_press',
      'tricep_extension',
      'lateral_raise',
      'crunch',
      'glute_bridge',
      'mountain_climber',
      'wall_sit',
      'romanian_deadlift',
      'leg_raise',
      'russian_twist',
      'high_knees',
    ];
  }

  public startExercise(name: string): void {
    this.currentExercise = name;
    this.lastResult = {
      ...this.lastResult,
      exercise_name: name,
      counter: 0,
      counter_left: 0,
      counter_right: 0,
      current_state: 'start',
      current_duration: 0.0,
      form_score: 100.0,
      avg_form_score: 100.0,
      form_grade: 'A',
      feedback_alerts: [],
      rep_completed: false,
    };
    this.lastSummary = null;

    const msg = JSON.stringify({ action: 'start', exercise: name });
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(msg);
    } else {
      this.pendingQueue.push(msg);
    }
  }

  public processLandmarksFlat(
    flatData: Float32Array,
    _width: number,
    _height: number,
    _timestampSec: number
  ): ExerciseResult {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // 33 landmarks * 4 floats = 132 float32 = 528 bytes binary transfer
      (this.ws as any).send(flatData.buffer);
    }
    return this.lastResult;
  }

  public stopExercise(): WorkoutSummary {
    const msg = JSON.stringify({ action: 'stop' });
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(msg);
    }

    return (
      this.lastSummary || {
        exercise_name: this.currentExercise,
        total_reps: this.lastResult.counter,
        counter_left: this.lastResult.counter_left,
        counter_right: this.lastResult.counter_right,
        total_duration_sec: this.lastResult.current_duration,
        avg_form_score: this.lastResult.avg_form_score,
        final_grade: this.lastResult.form_grade,
      }
    );
  }

  public resetCurrentExercise(): void {
    this.lastResult = {
      ...this.lastResult,
      counter: 0,
      counter_left: 0,
      counter_right: 0,
      current_state: 'start',
      current_duration: 0.0,
      form_score: 100.0,
      avg_form_score: 100.0,
      feedback_alerts: [],
      rep_completed: false,
    };
    const msg = JSON.stringify({ action: 'reset' });
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(msg);
    }
  }

  public getStatus(): ExerciseResult | null {
    return this.lastResult;
  }
}

export const posefitClient = new PoseClient();
