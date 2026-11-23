# PoseFit — Local-First AI Fitness Coach & Rep Counter

An optimized, local-first web application for real-time exercise form coaching, repetition counting, and biomechanical kinematics analysis powered by a **pure-Python (3.11+)** engine and a modern **React 19 + TypeScript** frontend.

---

## ⚡ Architectural Overview

```
[Webcam Stream / Pre-recorded MP4 File]
                 │
                 ▼
[Browser MediaPipe Pose (WebGL)]
                 │
                 ▼ (528-byte flat Float32Array @ 30-60 FPS)
    [WebSocket: /ws/pose?exercise=<id>]
                 │
                 ▼
[Python Kinematics Core (posefit/engine.py)]
                 ├── NumPy Vectorized Joint Angles (calculate_angle_2d / 3d)
                 ├── Temporal Landmark Smoothing (Exponential Moving Average)
                 ├── Deterministic Finite State Machine (FSM condition evaluator)
                 ├── Monotonic Repetition & Duration Counters
                 ├── Biomechanical Form Scoring (0–100% deduction engine)
                 └── Real-Time Form Correction Alerts & Guidance
                 │
                 ▼ (ExerciseResult JSON via orjson / standard JSON)
[React 19 Workout HUD]
                 ├── HTML5 Unified Canvas (Synchronous video frame + skeleton overlay)
                 ├── Real-Time Kinematic Degree Badges (Un-mirrored telemetry)
                 ├── Acoustic Feedback Chimes (Web Audio API)
                 └── Form Analytics & Workout Summary
```

### Key Architectural Tenets
1. **100% Local-First Privacy & Zero Cloud Egress**: Video feeds and landmark coordinates never leave your device. All computation runs locally on `127.0.0.1`.
2. **Pure-Python 3.11+ Core**: Cleanly split into a pure calculation core (`engine.py`, `geometry.py`, `filters.py`, `fsm.py`, `scoring.py`) and a thin async transport layer (`server.py`).
3. **Sub-Millisecond Engine Latency**: Batched NumPy vector kinematics evaluate joint angles, state machines, and form heuristics in **< 0.08 ms** per frame (over 11,500 frames/sec capacity).
4. **Offline Resilience**: MediaPipe models and assets are vendored locally under `web/public/mediapipe/pose/` for completely offline runtime operation without CDN dependencies.
5. **Cross-Platform Launcher**: Pure-Python launcher (`scripts/run.py`) works identically on Windows PowerShell/CMD, macOS, and Linux without shell-specific assumptions.

---

## 🎯 Operating Modes

* **Mode A (Default / Ultra-Lightweight)**:
  * The browser performs MediaPipe pose detection on-device using WebGL/WASM and streams only 33 coordinates per frame (flat 528-byte Float32Array) to the local Python engine over WebSocket.
  * Extremely low CPU & memory footprint (< 40 MB RSS, p50 latency < 0.1 ms). Ideal for low-spec dual-core laptops with integrated graphics.
* **Mode B (Optional Python-Side Vision)**:
  * The browser sends raw image frames, and Python performs pose estimation using OpenCV and MediaPipe Python (`pip install posefit[vision]`).
  * Features adaptive frame-skipping and bounded queues with drop-oldest backpressure to eliminate lag.

---

## 🏋️ Supported Exercises (18 Calibrated Movements)

All exercises are driven by typed declarative YAML kinematics definitions bundled in `posefit/src/posefit/assets/exercises/`:

| Movement Category | Calibrated Exercises |
| :--- | :--- |
| **Standard Repetitions** | Squat, Push-up, Deadlift, Shoulder Press, Lateral Raise, Tricep Dip, Leg Raise, Calf Raise, Glute Bridge |
| **Bilateral (Independent L/R)** | Bicep Curl, Hammer Curl, Forward Lunge, Side Lunge |
| **Isometric / Timed Hold** | Forearm Plank, Wall Sit |
| **High Tempo / Conditioning** | Jumping Jack, High Knees, Mountain Climber |

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python**: 3.11 or newer ([python.org](https://python.org))
* **Node.js**: v18+ ([nodejs.org](https://nodejs.org))

### 1. Install Python Core
```powershell
# From the repository root:
pip install -e posefit
```

### 2. Build Frontend Assets
```powershell
npm --workspace=web install
npm --workspace=web run build
```

### 3. Launch Application
```powershell
python scripts/run.py
```
`scripts/run.py` verifies the environment, spins up the local FastAPI server, serves the built frontend, and automatically opens your browser at **http://127.0.0.1:8000**.

---

## 🛠️ Developer & Testing Workflow

### Run Golden Parity Test Suite
Validates mathematical parity against 7 golden reference sequences (angles matching within 1e-4 degrees, identical frame-for-frame state transitions and rep counts):
```powershell
pytest posefit/tests -q
```

### Run Static Analysis & Type Checking
```powershell
ruff check posefit scripts
mypy posefit/src
```

### Run Engine Latency Benchmark
Reports ms/frame (p50/p95/p99), processed frames per second, and peak RSS memory:
```powershell
python posefit/bench/bench_engine.py
```
*Observed Benchmark Results (Intel i7 / Windows 11):*
* **p50 Latency:** `0.0756 ms`
* **p99 Latency:** `0.1569 ms`
* **Throughput:** `11,576 FPS`
* **Peak RSS:** `39.9 MB`

---

## 👥 Authors & Maintainers

* **Aman Yadav** — [amanyadav2030a@gmail.com](mailto:amanyadav2030a@gmail.com)
* **Hemang Bodana** — [hemangbodana123@gmail.com](mailto:hemangbodana123@gmail.com)

---

## 🛡️ License

MIT License. Designed for private, high-performance, real-time computer vision fitness coaching.
