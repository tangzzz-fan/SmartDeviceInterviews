"""
PPG FIR 带通参考实现（Python = 真值）。

口径：docs/02-算法对齐口径/fir-ppg-bandpass.md
- fs=25Hz, 0.5–4Hz, firwin 51 taps, hamming
- np.convolve(mode='same')
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy.signal import convolve, firwin


class FIRInputError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


FS = 25.0
F_LO = 0.5
F_HI = 4.0
NUMTAPS = 51


def design_bandpass_coeffs() -> np.ndarray:
    """设计带通 FIR 系数（float64）。"""
    # pass_zero=False → 带通；nyquist 归一化截止频率
    return firwin(
        NUMTAPS,
        [F_LO, F_HI],
        pass_zero=False,
        fs=FS,
        window="hamming",
    ).astype(np.float64)


def truncate_coeffs(coeffs: np.ndarray, significant_digits: int = 6) -> np.ndarray:
    """演示陷阱：截断有效位后阻带变差（不用于默认 golden）。"""
    return np.array([float(f"{c:.{significant_digits}g}") for c in coeffs], dtype=np.float64)


def fir_filter(x: Sequence[float], coeffs: np.ndarray) -> np.ndarray:
    if len(x) == 0:
        raise FIRInputError("empty", "empty input")
    arr = np.asarray(x, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise FIRInputError("non_finite", "input contains NaN/Inf")
    if not np.isfinite(coeffs).all():
        raise FIRInputError("non_finite", "coeffs contain NaN/Inf")
    # scipy.signal.convolve(..., mode='same')：输出长度 = len(x)
    # 注意：不要用 np.convolve 的 same（短输入时会变成 max(len(x), len(b))）
    return convolve(arr, coeffs, mode="same", method="direct")
