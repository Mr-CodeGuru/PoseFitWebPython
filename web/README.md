# PoseFit Web Frontend Client

Modern React 19 + TypeScript + Vite frontend client for the **PoseFit** computer vision AI fitness coaching system.

---

## ⚡ Architecture & Features

* **React 19 & TypeScript**: Strict types, discrete lifecycle hooks, zero unnecessary re-renders.
* **Tailwind CSS v4**: Hardware athletic console styling with dark mode and light mode tokens.
* **PoseClient (`src/wasm/posefitClient.ts`)**: Thin WebSocket client connecting to the local Python kinematic backend (`ws://127.0.0.1:8000/ws/pose`). Automatically handles exponential backoff reconnection and streams flat 528-byte Float32Array landmark buffers.
* **Unified CV Canvas (`src/cv/skeletonRenderer.ts`)**: Directly renders synchronous video frames and kinematic vector skeletons onto an HTML5 Canvas, completely eliminating GPU compositor collisions and black-screen playback bugs on Windows.
* **Offline-First MediaPipe Pose**: Vendored local assets under `public/mediapipe/pose/` ensure 100% offline functionality without CDN delays or telemetry tracking.

---

## 🚀 Development Setup

### Install Dependencies
```bash
npm install
```

### Run Vite Development Server
```bash
npm run dev
```
Accessible at [http://localhost:5173](http://localhost:5173). In development mode, Vite proxies `/api` and `/ws` requests directly to `http://127.0.0.1:8000`.

### Production Build
```bash
npm run build
```
Generates optimized, tree-shaken static production bundles in `dist/`.
