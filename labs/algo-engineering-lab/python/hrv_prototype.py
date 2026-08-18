"""
HRV 时域参考实现（Python = 真值生成器）。

公式与 docs/02-算法对齐口径/hrv-time-domain.md 对齐：
- SDNN / RMSSD 使用样本标准差口径（分母 N-1）
- 中间计算用 float64，避免 float32 累加漂移
- 本 case 不做伪差校正
"""

from __future__ import annotations

import math
from typing import Any


class HRVInputError(ValueError):
    """映射到 C 侧 ALGO_ERR_* 的语义错误。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code  # empty | too_short | non_finite


def _validate_rr(rr_ms: list[float]) -> None:
    if len(rr_ms) == 0:
        raise HRVInputError("empty", "RR series is empty")
    if len(rr_ms) < 2:
        raise HRVInputError("too_short", "need at least 2 RR intervals")
    if any(not math.isfinite(x) for x in rr_ms):
        raise HRVInputError("non_finite", "RR series contains NaN/Inf")


def hrv_time_domain(rr_ms: list[float]) -> dict[str, Any]:
    """返回 sdnn_ms / rmssd_ms / pnn50 / mean_rr_ms。"""
    _validate_rr(rr_ms)
    n = len(rr_ms)
    mean_rr = sum(rr_ms) / n

    # SDNN：样本标准差（ddof=1）
    var = sum((x - mean_rr) ** 2 for x in rr_ms) / (n - 1)
    sdnn = math.sqrt(var)

    # RMSSD：相邻差分的样本均方根
    diffs = [rr_ms[i + 1] - rr_ms[i] for i in range(n - 1)]
    rmssd = math.sqrt(sum(d * d for d in diffs) / (n - 1))

    # pNN50：|diff| > 50ms 的百分比
    over = sum(1 for d in diffs if abs(d) > 50.0)
    pnn50 = 100.0 * over / len(diffs)

    return {
        "sdnn_ms": sdnn,
        "rmssd_ms": rmssd,
        "pnn50": pnn50,
        "mean_rr_ms": mean_rr,
    }
