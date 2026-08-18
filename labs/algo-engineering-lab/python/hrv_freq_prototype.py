"""
HRV 频域参考实现（Python = 真值 + 中间快照）。

口径：docs/02-算法对齐口径/hrv-freq-domain.md
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np


class HRVFreqInputError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


FS = 4.0
MIN_RR = 16
LF_LO, LF_HI = 0.04, 0.15  # LF: [lo, hi)
HF_LO, HF_HI = 0.15, 0.40  # HF: [lo, hi]


def _validate(rr_ms: list[float]) -> np.ndarray:
    if len(rr_ms) == 0:
        raise HRVFreqInputError("empty", "empty")
    if len(rr_ms) < MIN_RR:
        raise HRVFreqInputError("too_short", "need >= 16 RR")
    arr = np.asarray(rr_ms, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise HRVFreqInputError("non_finite", "NaN/Inf")
    return arr


def _time_axis(rr_ms: np.ndarray) -> np.ndarray:
    t = np.zeros(len(rr_ms), dtype=np.float64)
    for i in range(1, len(rr_ms)):
        t[i] = t[i - 1] + rr_ms[i - 1] / 1000.0
    return t


def _hann(n: int) -> np.ndarray:
    if n == 1:
        return np.ones(1, dtype=np.float64)
    k = np.arange(n, dtype=np.float64)
    return 0.5 - 0.5 * np.cos(2.0 * math.pi * k / (n - 1))


def hrv_freq_domain(rr_ms: list[float]) -> dict[str, Any]:
    rr = _validate(rr_ms)
    t = _time_axis(rr)
    duration = float(t[-1])
    if duration <= 0:
        raise HRVFreqInputError("invalid_arg", "non-positive duration")

    # 重采样到 4Hz：网格不超过原始最后时刻
    n_out = int(duration * FS) + 1
    t_u = np.arange(n_out, dtype=np.float64) / FS
    t_u = t_u[t_u <= duration + 1e-12]
    resampled = np.interp(t_u, t, rr)

    mean = float(np.mean(resampled))
    detrended = resampled - mean

    w = _hann(len(detrended))
    windowed = detrended * w
    n = len(windowed)

    # rFFT：与 numpy 相同，不做 1/N
    spectrum = np.fft.rfft(windowed)
    power = (np.abs(spectrum) ** 2) / (n * n)
    freqs = np.fft.rfftfreq(n, d=1.0 / FS)

    lf_mask = (freqs >= LF_LO) & (freqs < LF_HI)
    hf_mask = (freqs >= HF_LO) & (freqs <= HF_HI)

    # 梯形积分；单点带宽用矩形近似
    def band_power(mask: np.ndarray) -> float:
        f = freqs[mask]
        p = power[mask]
        if len(f) == 0:
            return 0.0
        if len(f) == 1:
            return float(p[0] * (freqs[1] - freqs[0] if len(freqs) > 1 else 0.0))
        return float(np.trapezoid(p, f))

    lf = band_power(lf_mask)
    hf = band_power(hf_mask)
    if hf == 0.0:
        raise HRVFreqInputError("invalid_arg", "hf power is zero")
    ratio = lf / hf

    return {
        "lf": lf,
        "hf": hf,
        "lf_hf_ratio": ratio,
        "snapshots": {
            "resampled": resampled.tolist(),
            "detrended": detrended.tolist(),
            "windowed": windowed.tolist(),
            "psd": power.tolist(),
            "freqs": freqs.tolist(),
        },
    }
