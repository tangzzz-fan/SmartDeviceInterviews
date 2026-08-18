"""
HRV 伪差校正参考实现（Python = 真值生成器）。

口径：docs/02-算法对齐口径/hrv-artifact-correction.md
- 异常检测：局部邻域中位数偏差阈值（默认 120ms）+ 生理范围约束
- 回填：线性插值；单侧缺邻居时复制可用侧
"""

from __future__ import annotations

import math
from typing import Any

from .hrv_prototype import HRVInputError, hrv_time_domain

MIN_RR_MS = 300.0
MAX_RR_MS = 2000.0
THRESHOLD_MS = 120.0


def _validate_rr(rr_ms: list[float]) -> None:
    if len(rr_ms) == 0:
        raise HRVInputError("empty", "RR series is empty")
    if len(rr_ms) < 2:
        raise HRVInputError("too_short", "need at least 2 RR intervals")
    if any(not math.isfinite(x) for x in rr_ms):
        raise HRVInputError("non_finite", "RR series contains NaN/Inf")


def _local_median(values: list[float], i: int) -> float:
    """取 i 附近有效邻域（不含自身）的中位数。"""
    neighbors: list[float] = []
    for k in (i - 2, i - 1, i + 1, i + 2):
        if 0 <= k < len(values):
            neighbors.append(values[k])
    if not neighbors:
        return values[i]
    neighbors.sort()
    m = len(neighbors)
    if m % 2 == 1:
        return neighbors[m // 2]
    return 0.5 * (neighbors[m // 2 - 1] + neighbors[m // 2])


def detect_artifacts(rr_ms: list[float], threshold_ms: float = THRESHOLD_MS) -> list[int]:
    mask = [0] * len(rr_ms)
    for i, rr in enumerate(rr_ms):
        if rr < MIN_RR_MS or rr > MAX_RR_MS:
            mask[i] = 1
            continue
        median = _local_median(rr_ms, i)
        if abs(rr - median) > threshold_ms:
            mask[i] = 1
    return mask


def correct_artifacts(rr_ms: list[float], threshold_ms: float = THRESHOLD_MS) -> dict[str, Any]:
    _validate_rr(rr_ms)
    n = len(rr_ms)
    raw = list(rr_ms)
    mask = detect_artifacts(raw, threshold_ms)
    corrected = list(raw)

    for i in range(n):
        if mask[i] == 0:
            continue
        left = i - 1
        while left >= 0 and mask[left] == 1:
            left -= 1
        right = i + 1
        while right < n and mask[right] == 1:
            right += 1

        if left >= 0 and right < n:
            t = (i - left) / (right - left)
            corrected[i] = corrected[left] + t * (corrected[right] - corrected[left])
        elif left >= 0:
            corrected[i] = corrected[left]
        elif right < n:
            corrected[i] = corrected[right]
        else:
            corrected[i] = raw[i]

    td = hrv_time_domain(corrected)
    return {
        "rr_raw": raw,
        "artifact_mask": mask,
        "rr_corrected": corrected,
        "sdnn_ms": td["sdnn_ms"],
        "rmssd_ms": td["rmssd_ms"],
        "pnn50": td["pnn50"],
        "mean_rr_ms": td["mean_rr_ms"],
    }
