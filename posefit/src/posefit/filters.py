"""Temporal smoothing filters, moving average buffers, and 1-Euro adaptive filtering.

TemporalSmoother exponential moving average angle filter.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np


class TemporalSmoother:
    """Moving average temporal smoothing filter for joint angles.

    Exponential moving average filter:
    - Window size N (default 3)
    - Insufficient history (< N) averages all currently available values
    - Exceeding window drops the oldest sample
    - History is maintained per angle name
    """

    __slots__ = ("_window_size", "_enabled", "_history")

    def __init__(self, window_size: int = 3, enabled: bool = True) -> None:
        self._window_size = max(1, window_size)
        self._enabled = enabled
        self._history: dict[str, deque[float]] = {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    @property
    def window_size(self) -> int:
        return self._window_size

    def smooth(self, angle_name: str, raw_angle: float) -> float:
        """Applies moving average smoothing to raw_angle for the given angle_name."""
        if not self._enabled:
            return raw_angle

        q = self._history.setdefault(angle_name, deque(maxlen=self._window_size))
        q.append(raw_angle)
        return sum(q) / len(q)

    def reset(self) -> None:
        """Clears history for all angles."""
        self._history.clear()


class OneEuroFilter:
    """1€ Filter for noisy kinematic signals (Casiez et al., CHI 2012).

    Adapts cutoff frequency based on movement speed: reduces jitter at low velocity
    and reduces lag at high velocity.
    """

    __slots__ = ("_min_cutoff", "_beta", "_d_cutoff", "_x_prev", "_dx_prev", "_t_prev")

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_prev: float | None = None
        self._dx_prev: float = 0.0
        self._t_prev: float | None = None

    def _smoothing_factor(self, te: float, cutoff: float) -> float:
        r = 2.0 * math.pi * cutoff * te
        return r / (r + 1.0)

    def filter(self, x: float, timestamp_sec: float) -> float:
        """Filters input scalar sample x at the given timestamp."""
        if self._x_prev is None or self._t_prev is None:
            self._x_prev = x
            self._dx_prev = 0.0
            self._t_prev = timestamp_sec
            return x

        te = timestamp_sec - self._t_prev
        if te <= 0.0:
            return self._x_prev

        # Estimate derivative
        a_d = self._smoothing_factor(te, self._d_cutoff)
        dx = (x - self._x_prev) / te
        dx_hat = a_d * dx + (1.0 - a_d) * self._dx_prev

        # Compute adaptive cutoff
        cutoff = self._min_cutoff + self._beta * abs(dx_hat)
        a = self._smoothing_factor(te, cutoff)

        x_hat = a * x + (1.0 - a) * self._x_prev

        self._x_prev = x_hat
        self._dx_prev = dx_hat
        self._t_prev = timestamp_sec
        return x_hat

    def reset(self) -> None:
        """Resets filter memory."""
        self._x_prev = None
        self._dx_prev = 0.0
        self._t_prev = None


class EMAFilter:
    """Exponential Moving Average filter."""

    __slots__ = ("_alpha", "_val")

    def __init__(self, alpha: float = 0.3) -> None:
        self._alpha = max(0.0, min(1.0, alpha))
        self._val: float | None = None

    def filter(self, x: float) -> float:
        if self._val is None:
            self._val = x
            return x
        self._val = self._alpha * x + (1.0 - self._alpha) * self._val
        return self._val

    def reset(self) -> None:
        self._val = None


class RingBuffer:
    """Fixed-capacity ring buffer backed by NumPy array."""

    __slots__ = ("_capacity", "_data", "_size", "_head")

    def __init__(self, capacity: int) -> None:
        self._capacity = max(1, capacity)
        self._data = np.zeros(self._capacity, dtype=np.float64)
        self._size = 0
        self._head = 0

    def append(self, val: float) -> None:
        self._data[self._head] = val
        self._head = (self._head + 1) % self._capacity
        if self._size < self._capacity:
            self._size += 1

    def mean(self) -> float:
        if self._size == 0:
            return 0.0
        return float(np.mean(self._data[: self._size]))

    def clear(self) -> None:
        self._size = 0
        self._head = 0
        self._data.fill(0.0)
