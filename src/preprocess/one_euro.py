# ai_fitness_coach/src/preprocess/one_euro.py
"""
Minimal implementation of the One-Euro Filter
from Casiez et al. (CHI 2012).

Call  filter(value, t)  for each new sample.
"""

import math


class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self._x_prev = None          # last smoothed value
        self._dx_prev = 0.0          # last smoothed derivative
        self._t_prev = None          # last timestamp (s)

    # ---------- helpers ----------
    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def _lowpass(self, x, x_prev, alpha):
        return alpha * x + (1.0 - alpha) * x_prev if x_prev is not None else x

    # ---------- public API ----------
    def filter(self, x, t):
        if self._t_prev is None:
            # first call → initialise and return raw value
            self._t_prev, self._x_prev = t, x
            return x

        dt = t - self._t_prev
        self._t_prev = t

        # 1. derivative of the signal
        dx = (x - self._x_prev) / dt
        alpha_d = self._alpha(self.d_cutoff, dt)
        dx_hat = self._lowpass(dx, self._dx_prev, alpha_d)
        self._dx_prev = dx_hat

        # 2. adapt cutoff
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)

        # 3. smooth the signal
        alpha = self._alpha(cutoff, dt)
        x_hat = self._lowpass(x, self._x_prev, alpha)
        self._x_prev = x_hat
        return x_hat
