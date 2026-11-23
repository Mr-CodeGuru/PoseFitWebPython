"""NumPy-vectorized 2D kinematics, vector trigonometry, and coordinate transformations.

Vectorized joint angle calculation and pixel projection.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from posefit.config import (
    LANDMARK_NAME_TO_INDEX,
)

# Precomputed index mappings for fast lookup
NUM_TOTAL_LANDMARKS: int = 33
LANDMARK_DIMS: int = 4  # x, y, z, visibility


def calculate_angle_2d(
    p1: tuple[float | int, float | int],
    p2: tuple[float | int, float | int],
    p3: tuple[float | int, float | int],
) -> float:
    """Calculates the 2D planar angle in degrees formed by three points (p1, p2, p3).

    `p2` is the vertex (joint center).
    Planar 2D joint angle calculation:
    - Vector BA = p1 - p2
    - Vector BC = p3 - p2
    - dot = BA . BC
    - norm1 = ||BA||, norm2 = ||BC||
    - if norm1 == 0.0 or norm2 == 0.0 -> returns 0.0
    - cos_angle = clamp(dot / (norm1 * norm2), -1.0, 1.0)
    - angle = acos(cos_angle) in degrees
    """
    v1_x = float(p1[0]) - float(p2[0])
    v1_y = float(p1[1]) - float(p2[1])
    v2_x = float(p3[0]) - float(p2[0])
    v2_y = float(p3[1]) - float(p2[1])

    dot = v1_x * v2_x + v1_y * v2_y
    norm1 = math.sqrt(v1_x * v1_x + v1_y * v1_y)
    norm2 = math.sqrt(v2_x * v2_x + v2_y * v2_y)

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    cos_angle = dot / (norm1 * norm2)
    # Clamp to avoid floating point precision out-of-domain errors
    if cos_angle > 1.0:
        cos_angle = 1.0
    elif cos_angle < -1.0:
        cos_angle = -1.0

    return math.degrees(math.acos(cos_angle))


def batch_calculate_angles_2d(
    coords: np.ndarray,
    triplets: np.ndarray,
) -> np.ndarray:
    """Vectorized calculation of 2D joint angles across multiple triplets.

    Args:
        coords: ndarray of shape (N, 2), containing 2D (x, y) coordinates for N landmarks.
        triplets: ndarray of shape (K, 3), containing (p1_idx, vertex_idx, p3_idx) integers.

    Returns:
        ndarray of shape (K,) with angles in degrees in [0.0, 180.0].
    """
    if len(triplets) == 0:
        return np.empty((0,), dtype=np.float64)

    p1_indices = triplets[:, 0]
    p2_indices = triplets[:, 1]
    p3_indices = triplets[:, 2]

    # Vectors BA = p1 - p2, BC = p3 - p2
    v1 = coords[p1_indices] - coords[p2_indices]  # shape (K, 2)
    v2 = coords[p3_indices] - coords[p2_indices]  # shape (K, 2)

    # Dot products
    dot = np.sum(v1 * v2, axis=1)

    # Norms
    norm1 = np.linalg.norm(v1, axis=1)
    norm2 = np.linalg.norm(v2, axis=1)

    denom = norm1 * norm2
    zero_mask = (norm1 == 0.0) | (norm2 == 0.0)

    # Safe division avoiding warnings
    with np.errstate(divide="ignore", invalid="ignore"):
        safe_denom = np.where(zero_mask, 1.0, denom)
        cos_angle = np.clip(dot / safe_denom, -1.0, 1.0)
        angles = np.degrees(np.arccos(cos_angle))
        angles[zero_mask] = 0.0

    return angles


def flat_to_pixel_coords(
    flat_data: Sequence[float] | np.ndarray,
    width: int,
    height: int,
) -> dict[str, tuple[int, int]]:
    """Converts a flat Float32Array [x0, y0, z0, v0, ...] of 33 landmarks to pixel coordinates.

    Projects normalized landmark coordinates to pixel space:
    `px = int(lm.x * width)`
    `py = int(lm.y * height)`
    """
    coords: dict[str, tuple[int, int]] = {}
    for name, idx in LANDMARK_NAME_TO_INDEX.items():
        offset = idx * 4
        if offset + 1 < len(flat_data):
            x = flat_data[offset]
            y = flat_data[offset + 1]
            coords[name] = (int(x * width), int(y * height))
    return coords


def flat_to_coord_matrix(
    flat_data: Sequence[float] | np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """Converts a flat 33-landmark coordinate array to an (N, 2) pixel coordinate NumPy array."""
    arr = np.asarray(flat_data, dtype=np.float32)
    if len(arr) < 33 * 4:
        raise ValueError(
            f"Flat landmark buffer must contain at least 132 elements (got {len(arr)})"
        )
    x = (arr[0::4][:33] * width).astype(np.int32)
    y = (arr[1::4][:33] * height).astype(np.int32)
    return np.column_stack((x, y))


def compute_distance_2d(
    p1: tuple[float | int, float | int],
    p2: tuple[float | int, float | int],
) -> float:
    """Calculates 2D Euclidean distance between two points."""
    dx = float(p1[0]) - float(p2[0])
    dy = float(p1[1]) - float(p2[1])
    return math.sqrt(dx * dx + dy * dy)
