"""
多通道同步与时间戳漂移校正参考实现（Python = 真值）。

口径：docs/02-算法对齐口径/multi-channel-sync.md
"""

from __future__ import annotations

import math
from typing import Any


def rebuild_timeline(
    packets: list[dict[str, Any]],
    channels: list[str],
    dt_ref: float,
    *,
    zero_fill: bool = True,
) -> dict[str, Any]:
    if not math.isfinite(dt_ref) or dt_ref <= 0:
        raise ValueError("invalid dt_ref")

    # channel -> index -> value / present
    values: dict[str, dict[int, float]] = {ch: {} for ch in channels}
    present: dict[str, dict[int, int]] = {ch: {} for ch in channels}
    max_idx = -1

    # 按 seq 排序模拟接收重排恢复
    sorted_packets = sorted(packets, key=lambda p: int(p["seq"]))
    for p in sorted_packets:
        ch = str(p["channel_id"])
        if ch not in values:
            continue
        t0 = float(p["t0"])
        dt_local = float(p["dt"])
        samples = [float(x) for x in p["samples"]]
        for i, x in enumerate(samples):
            t = t0 + i * dt_local
            idx = int(round(t / dt_ref))
            if idx < 0:
                continue
            values[ch][idx] = x
            present[ch][idx] = 1
            if idx > max_idx:
                max_idx = idx

    if max_idx < 0:
        return {
            "timeline": [],
            "aligned": {ch: [] for ch in channels},
            "mask": {ch: [] for ch in channels},
        }

    timeline = [k * dt_ref for k in range(max_idx + 1)]
    aligned: dict[str, list[float]] = {}
    mask: dict[str, list[int]] = {}
    for ch in channels:
        arr: list[float] = []
        m: list[int] = []
        for i in range(max_idx + 1):
            if i in values[ch]:
                arr.append(values[ch][i])
                m.append(1)
            else:
                arr.append(0.0 if zero_fill else float("nan"))
                m.append(0)
        aligned[ch] = arr
        mask[ch] = m

    return {
        "timeline": timeline,
        "aligned": aligned,
        "mask": mask,
    }
