"""
睡眠分期后处理参考实现（Python = 真值）。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

STAGES = ["W", "N1", "N2", "N3", "REM"]


def _argmax_stage(prob: list[float]) -> str:
    idx = max(range(len(prob)), key=lambda i: prob[i])
    return STAGES[idx]


def _majority3(stages: list[str]) -> list[str]:
    if len(stages) < 3:
        return stages[:]
    out = stages[:]
    for i in range(1, len(stages) - 1):
        window = [stages[i - 1], stages[i], stages[i + 1]]
        c = Counter(window).most_common(1)[0][0]
        out[i] = c
    return out


def _collapse_singletons(stages: list[str]) -> list[str]:
    if len(stages) < 3:
        return stages[:]
    out = stages[:]
    for i in range(1, len(stages) - 1):
        if out[i - 1] == out[i + 1] and out[i] != out[i - 1]:
            out[i] = out[i - 1]
    return out


def _sleep_metrics(stages: list[str]) -> dict[str, Any]:
    # 30s/epoch
    total_epochs = len(stages)
    sleep_epochs = sum(1 for s in stages if s != "W")
    tst_min = sleep_epochs * 0.5
    sol_epoch = next((i for i, s in enumerate(stages) if s != "W"), total_epochs)
    sol_min = sol_epoch * 0.5
    return {"total_epochs": total_epochs, "sleep_epochs": sleep_epochs, "tst_min": tst_min, "sol_min": sol_min}


def postprocess(prob_seq: list[list[float]]) -> dict[str, Any]:
    if len(prob_seq) == 0:
        return {"raw_stages": [], "smoothed_stages": [], "metrics": _sleep_metrics([])}

    raw = [_argmax_stage(p) for p in prob_seq]
    # 两步平滑：3 点多数 + 单点折叠
    s1 = _majority3(raw)
    smoothed = _collapse_singletons(s1)
    return {"raw_stages": raw, "smoothed_stages": smoothed, "metrics": _sleep_metrics(smoothed)}
