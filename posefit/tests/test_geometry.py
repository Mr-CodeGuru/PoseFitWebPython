"""Unit tests for geometry, 2D vector trigonometry, and vectorized batch operations.

Unit tests for 2D/3D angle calculation and landmark pixel projection.
"""

from __future__ import annotations

import numpy as np

from posefit.geometry import (
    batch_calculate_angles_2d,
    calculate_angle_2d,
    compute_distance_2d,
    flat_to_pixel_coords,
)

EPSILON: float = 1e-4


def test_angle_90_degrees() -> None:
    # Right angle: p1=(0, 10), p2=(0, 0), p3=(10, 0)
    angle = calculate_angle_2d((0, 10), (0, 0), (10, 0))
    assert abs(angle - 90.0) < EPSILON, f"Expected 90.0, got {angle}"


def test_angle_180_degrees() -> None:
    # Straight line: p1=(-10, 0), p2=(0, 0), p3=(10, 0)
    angle = calculate_angle_2d((-10, 0), (0, 0), (10, 0))
    assert abs(angle - 180.0) < EPSILON, f"Expected 180.0, got {angle}"


def test_angle_0_degrees() -> None:
    # Coincident rays: p1=(10, 0), p2=(0, 0), p3=(10, 0)
    angle = calculate_angle_2d((10, 0), (0, 0), (10, 0))
    assert abs(angle - 0.0) < EPSILON, f"Expected 0.0, got {angle}"


def test_angle_45_degrees() -> None:
    # 45 degrees: p1=(10, 0), p2=(0, 0), p3=(10, 10)
    angle = calculate_angle_2d((10, 0), (0, 0), (10, 10))
    assert abs(angle - 45.0) < EPSILON, f"Expected 45.0, got {angle}"


def test_angle_zero_vectors_degenerate() -> None:
    # Degenerate point: p1 == p2
    assert calculate_angle_2d((0, 0), (0, 0), (10, 0)) == 0.0
    # Degenerate point: p3 == p2
    assert calculate_angle_2d((10, 0), (0, 0), (0, 0)) == 0.0
    # All points identical
    assert calculate_angle_2d((5, 5), (5, 5), (5, 5)) == 0.0


def test_angle_nearly_zero_vectors() -> None:
    angle = calculate_angle_2d((1e-12, 0.0), (0.0, 0.0), (0.0, 1e-12))
    assert abs(angle - 90.0) < 1e-2, f"Expected ~90.0, got {angle}"


def test_floating_point_edge_cases_clamping() -> None:
    # Parallel vectors where numerical noise could cause dot/(norm1*norm2) > 1.0 without clamp
    p1 = (1000.0, 1000.0)
    p2 = (0.0, 0.0)
    p3 = (1000.000000001, 1000.000000001)
    angle = calculate_angle_2d(p1, p2, p3)
    assert abs(angle - 0.0) < EPSILON, f"Expected ~0.0, got {angle}"


def test_batch_calculate_angles_matches_scalar() -> None:
    # Multiple triplets calculated simultaneously
    coords = np.array(
        [
            [0.0, 10.0],  # 0
            [0.0, 0.0],   # 1
            [10.0, 0.0],  # 2
            [-10.0, 0.0], # 3
            [10.0, 10.0], # 4
        ],
        dtype=np.float64,
    )
    triplets = np.array(
        [
            [0, 1, 2],  # 90 deg
            [3, 1, 2],  # 180 deg
            [2, 1, 2],  # 0 deg
            [2, 1, 4],  # 45 deg
            [1, 1, 2],  # degenerate -> 0 deg
        ],
        dtype=np.int32,
    )

    batch_res = batch_calculate_angles_2d(coords, triplets)

    assert abs(batch_res[0] - 90.0) < EPSILON
    assert abs(batch_res[1] - 180.0) < EPSILON
    assert abs(batch_res[2] - 0.0) < EPSILON
    assert abs(batch_res[3] - 45.0) < EPSILON
    assert abs(batch_res[4] - 0.0) < EPSILON


def test_flat_to_pixel_coords_matches_rust() -> None:
    flat = [0.0] * (33 * 4)
    # Nose (idx 0) at x=0.5, y=0.25
    flat[0] = 0.5
    flat[1] = 0.25
    flat[2] = 0.0
    flat[3] = 1.0

    coords = flat_to_pixel_coords(flat, 1280, 720)
    assert coords["nose"] == (640, 180)


def test_compute_distance_2d() -> None:
    dist = compute_distance_2d((0, 0), (3, 4))
    assert abs(dist - 5.0) < 1e-6
