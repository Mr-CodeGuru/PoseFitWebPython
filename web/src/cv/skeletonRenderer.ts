import type { ExerciseResult } from '../types/posefit';

const POSE_CONNECTIONS: [number, number][] = [
  // Torso
  [11, 12],
  [11, 23],
  [12, 24],
  [23, 24],
  // Left arm
  [11, 13],
  [13, 15],
  // Right arm
  [12, 14],
  [14, 16],
  // Left leg
  [23, 25],
  [25, 27],
  [27, 29],
  [29, 31],
  [27, 31],
  // Right leg
  [24, 26],
  [26, 28],
  [28, 30],
  [30, 32],
  [28, 32],
];

export class SkeletonRenderer {
  /**
   * Draws both the video frame and kinematic skeleton onto the canvas.
   * If isMirrored is true (e.g. webcam), the video frame and limbs mirror,
   * while angle telemetry text badges stay readable and un-mirrored.
   */
  public static draw(
    ctx: CanvasRenderingContext2D,
    videoSource: HTMLVideoElement | null,
    landmarks: any[],
    canvasWidth: number,
    canvasHeight: number,
    exerciseResult?: ExerciseResult | null,
    isMirrored: boolean = false
  ): void {
    if (canvasWidth <= 0 || canvasHeight <= 0) return;

    // 1. Draw video background or clear
    if (videoSource && videoSource.readyState >= 2) {
      if (isMirrored) {
        ctx.save();
        ctx.translate(canvasWidth, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(videoSource, 0, 0, canvasWidth, canvasHeight);
        ctx.restore();
      } else {
        ctx.drawImage(videoSource, 0, 0, canvasWidth, canvasHeight);
      }
    } else {
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    }

    if (!landmarks || landmarks.length < 33) return;

    // 2. Functional athletic color palette based on form score
    // Emerald = solid alignment (>=80), Amber = correction warning (60-79), Red = critical error (<60)
    let strokeColor = '#10b981'; // Emerald-500
    let jointColor = '#34d399';  // Emerald-400
    if (exerciseResult) {
      if (exerciseResult.form_score < 60) {
        strokeColor = '#f43f5e'; // Rose-500
        jointColor = '#fb7185';
      } else if (exerciseResult.form_score < 80) {
        strokeColor = '#f59e0b'; // Amber-500
        jointColor = '#fbbf24';
      }
    }

    // Draw Kinematic Vectors / Bones and Landmark Joints
    // If mirrored, apply horizontal flip context so coordinates match mirrored video
    if (isMirrored) {
      ctx.save();
      ctx.translate(canvasWidth, 0);
      ctx.scale(-1, 1);
    }

    ctx.lineWidth = 3.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    for (const [startIdx, endIdx] of POSE_CONNECTIONS) {
      const p1 = landmarks[startIdx];
      const p2 = landmarks[endIdx];

      if (
        !p1 ||
        !p2 ||
        (p1.visibility ?? 1.0) < 0.35 ||
        (p2.visibility ?? 1.0) < 0.35
      ) {
        continue;
      }

      ctx.beginPath();
      ctx.strokeStyle = strokeColor;
      ctx.moveTo(p1.x * canvasWidth, p1.y * canvasHeight);
      ctx.lineTo(p2.x * canvasWidth, p2.y * canvasHeight);
      ctx.stroke();
    }

    // Draw Landmark Joints (11-32 body joints)
    for (let i = 11; i < landmarks.length; i++) {
      const p = landmarks[i];
      if ((p.visibility ?? 1.0) < 0.35) continue;

      const cx = p.x * canvasWidth;
      const cy = p.y * canvasHeight;

      // Outer joint border
      ctx.beginPath();
      ctx.arc(cx, cy, 5, 0, 2 * Math.PI);
      ctx.fillStyle = jointColor;
      ctx.fill();

      // Inner high-contrast center
      ctx.beginPath();
      ctx.arc(cx, cy, 2, 0, 2 * Math.PI);
      ctx.fillStyle = '#090d16';
      ctx.fill();
    }

    if (isMirrored) {
      ctx.restore();
    }

    // 3. Draw Joint Angle Badges (always rendered text-forward, never backwards)
    if (exerciseResult && exerciseResult.angles) {
      ctx.font = '600 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const getX = (p: any) =>
        isMirrored ? (1 - p.x) * canvasWidth : p.x * canvasWidth;
      const getY = (p: any) => p.y * canvasHeight;

      // Left Knee
      const kneeLeft = landmarks[25];
      if (kneeLeft && (kneeLeft.visibility ?? 1.0) >= 0.5 && exerciseResult.angles['left_knee']) {
        const val = Math.round(exerciseResult.angles['left_knee']);
        this.drawAngleBadge(ctx, getX(kneeLeft), getY(kneeLeft) - 16, `${val}°`);
      }

      // Right Knee
      const kneeRight = landmarks[26];
      if (kneeRight && (kneeRight.visibility ?? 1.0) >= 0.5 && exerciseResult.angles['right_knee']) {
        const val = Math.round(exerciseResult.angles['right_knee']);
        this.drawAngleBadge(ctx, getX(kneeRight), getY(kneeRight) - 16, `${val}°`);
      }

      // Left Elbow
      const elbowLeft = landmarks[13];
      if (elbowLeft && (elbowLeft.visibility ?? 1.0) >= 0.5 && exerciseResult.angles['left']) {
        const val = Math.round(exerciseResult.angles['left']);
        this.drawAngleBadge(ctx, getX(elbowLeft), getY(elbowLeft) - 16, `${val}°`);
      }

      // Right Elbow
      const elbowRight = landmarks[14];
      if (elbowRight && (elbowRight.visibility ?? 1.0) >= 0.5 && exerciseResult.angles['right']) {
        const val = Math.round(exerciseResult.angles['right']);
        this.drawAngleBadge(ctx, getX(elbowRight), getY(elbowRight) - 16, `${val}°`);
      }
    }
  }

  private static drawAngleBadge(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    text: string
  ): void {
    const textWidth = ctx.measureText(text).width;
    const paddingX = 6;
    const height = 18;
    const width = textWidth + paddingX * 2;

    ctx.fillStyle = 'rgba(9, 13, 22, 0.9)';
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.roundRect(x - width / 2, y - height / 2, width, height, 3);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#e2e8f0';
    ctx.fillText(text, x, y);
  }
}
