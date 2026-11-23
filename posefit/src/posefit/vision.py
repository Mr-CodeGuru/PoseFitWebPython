"""Mode B Vision pipeline: OpenCV frame decoding and MediaPipe Python pose estimation.

Only imported when Mode B is activated (`pip install posefit[vision]`).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("posefit.vision")


class MediaPipePoseEstimator:
    """Mode B on-device pose estimation using MediaPipe Python."""

    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5) -> None:
        try:
            import cv2  # noqa: F401
            import mediapipe as mp  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "Mode B requires opencv and mediapipe. Install via `pip install posefit[vision]`."
            ) from exc

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )

    def estimate_from_bytes(
        self, image_bytes: bytes, width: int = 1280, height: int = 720
    ) -> list[float] | None:
        """Decodes image bytes (JPEG/WebP) and extracts 33 flat landmarks (x, y, z, visibility)."""
        import cv2

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        # MediaPipe expects RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results: Any = self.pose.process(img_rgb)

        if not results.pose_landmarks:
            return None

        flat: list[float] = []
        for lm in results.pose_landmarks.landmark:
            flat.extend([
                float(lm.x),
                float(lm.y),
                float(lm.z),
                float(lm.visibility if hasattr(lm, "visibility") else 1.0),
            ])
        return flat

    def close(self) -> None:
        """Releases MediaPipe C++ graph memory."""
        if hasattr(self, "pose") and self.pose:
            self.pose.close()
