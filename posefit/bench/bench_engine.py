"""PoseFit kinematics benchmark suite.

Measures Mode A latency distribution (p50, p95, p99), frame throughput (FPS),
and memory footprint (peak RSS) using synthetic trigonometric kinematics.
"""

from __future__ import annotations

import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import psutil  # type: ignore[import-untyped]

# Ensure posefit is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from posefit.engine import PoseEngine  # noqa: E402


def generate_synthetic_squat_frames(n_frames: int = 1000) -> list[tuple[np.ndarray, float]]:
    """Generates synthetic 33-landmark frames simulating sinusoidal squats."""
    frames: list[tuple[np.ndarray, float]] = []
    for i in range(n_frames):
        ts = i * 0.033  # 30 fps
        phase = math.sin(i * 0.05)  # oscillation between standing and deep squat
        knee_y = 0.65 + 0.15 * phase
        hip_y = 0.50 + 0.10 * phase

        flat = np.zeros(33 * 4, dtype=np.float32)
        # Shoulder
        flat[11 * 4] = 0.5
        flat[11 * 4 + 1] = 0.2
        flat[11 * 4 + 3] = 1.0

        # Hip
        flat[23 * 4] = 0.5
        flat[23 * 4 + 1] = hip_y
        flat[23 * 4 + 3] = 1.0

        # Knee
        flat[25 * 4] = 0.5
        flat[25 * 4 + 1] = knee_y
        flat[25 * 4 + 3] = 1.0

        # Ankle
        flat[27 * 4] = 0.5
        flat[27 * 4 + 1] = 0.95
        flat[27 * 4 + 3] = 1.0

        # Right side
        flat[12 * 4] = 0.5
        flat[12 * 4 + 1] = 0.2
        flat[12 * 4 + 3] = 1.0
        flat[24 * 4] = 0.5
        flat[24 * 4 + 1] = hip_y
        flat[24 * 4 + 3] = 1.0
        flat[26 * 4] = 0.5
        flat[26 * 4 + 1] = knee_y
        flat[26 * 4 + 3] = 1.0
        flat[28 * 4] = 0.5
        flat[28 * 4 + 1] = 0.95
        flat[28 * 4 + 3] = 1.0

        frames.append((flat, ts))
    return frames


def run_benchmark(num_frames: int = 1000, exercise: str = "squat") -> dict[str, float]:
    """Runs the latency, throughput, and RSS benchmark and prints formatted report."""
    process = psutil.Process(os.getpid())
    rss_start_mb = process.memory_info().rss / (1024 * 1024)

    engine = PoseEngine()
    engine.register_all_bundled_exercises()
    engine.start_exercise(exercise)

    frames = generate_synthetic_squat_frames(num_frames)

    # Warmup
    for flat, ts in frames[:50]:
        engine.process_landmarks_flat(flat, 1000, 1000, ts)
    engine.reset()

    # Measured run
    latencies_us: list[float] = []
    total_start = time.perf_counter()

    for flat, ts in frames:
        t0 = time.perf_counter_ns()
        engine.process_landmarks_flat(flat, 1000, 1000, ts)
        t1 = time.perf_counter_ns()
        latencies_us.append((t1 - t0) / 1000.0)

    total_elapsed = time.perf_counter() - total_start
    rss_end_mb = process.memory_info().rss / (1024 * 1024)

    latencies_ms = np.array(latencies_us) / 1000.0
    p50 = float(np.percentile(latencies_ms, 50))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    fps = num_frames / total_elapsed

    print("==================================================")
    print(f" PoseFit Engine Benchmark ({num_frames} frames, exercise: {exercise})")
    print("==================================================")
    print(" Per-frame Engine Latency:")
    print(f"   p50:  {p50:.4f} ms  (Target: < 1.0 ms)")
    print(f"   p95:  {p95:.4f} ms")
    print(f"   p99:  {p99:.4f} ms  (Target: < 3.0 ms)")
    print(f" Throughput: {fps:.1f} frames/sec")
    print(" Memory Footprint:")
    print(f"   Idle/Start RSS: {rss_start_mb:.1f} MB")
    print(f"   Peak/End RSS:   {rss_end_mb:.1f} MB  (Target: < 80.0 MB)")
    print("==================================================")

    return {
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "fps": fps,
        "rss_mb": rss_end_mb,
    }


if __name__ == "__main__":
    run_benchmark()
