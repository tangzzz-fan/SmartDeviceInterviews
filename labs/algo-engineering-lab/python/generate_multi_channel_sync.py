"""
生成多通道同步与漂移校正 golden。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .multi_channel_sync_prototype import rebuild_timeline

SEED = 42
CASE = "multi_channel_sync"
DT = 0.04  # 25Hz


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _synth_packets(
    *,
    n: int,
    drift_ppm_acc: float,
    drop_ratio: float,
    disorder: bool,
    rng: random.Random,
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    seq = 0
    acc_dt = DT * (1.0 + drift_ppm_acc * 1e-6)
    for i in range(n):
        # ppg channel
        packets.append(
            {
                "seq": seq,
                "channel_id": "ppg",
                "sample_count": 1,
                "t0": i * DT,
                "dt": DT,
                "samples": [1000.0 + i],
            }
        )
        seq += 1
        # acc channel
        packets.append(
            {
                "seq": seq,
                "channel_id": "acc",
                "sample_count": 1,
                "t0": i * acc_dt,
                "dt": acc_dt,
                "samples": [2000.0 + i],
            }
        )
        seq += 1

    if drop_ratio > 0:
        keep: list[dict[str, Any]] = []
        for p in packets:
            if rng.random() >= drop_ratio:
                keep.append(p)
        packets = keep

    if disorder:
        rng.shuffle(packets)
    return packets


def _record(idx: int, category: str, pathology: str, packets: list[dict[str, Any]]) -> dict[str, Any]:
    out = rebuild_timeline(packets, ["ppg", "acc"], DT, zero_fill=True)
    return {
        "id": f"mcs_{idx:03d}",
        "case": CASE,
        "category": category,
        "pathology": pathology,
        "input": {
            "channels": ["ppg", "acc"],
            "dt_ref": DT,
            "zero_fill": True,
            "packets": packets,
        },
        "expected": {
            "timeline": out["timeline"],
            "aligned": out["aligned"],
            "mask": out["mask"],
            "ok": True,
        },
        "meta": {"seed": SEED, "generator": "python/multi_channel_sync_prototype.py"},
    }


def build_dataset() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []
    i = 1

    # normal
    for _ in range(12):
        p = _synth_packets(n=30, drift_ppm_acc=0.0, drop_ratio=0.0, disorder=False, rng=rng)
        rows.append(_record(i, "normal", "none", p))
        i += 1

    # pathological: drift
    for _ in range(10):
        p = _synth_packets(n=30, drift_ppm_acc=80.0, drop_ratio=0.0, disorder=False, rng=rng)
        rows.append(_record(i, "pathological", "clock_drift", p))
        i += 1

    # pathological: drop + disorder
    for _ in range(10):
        p = _synth_packets(n=30, drift_ppm_acc=100.0, drop_ratio=0.08, disorder=True, rng=rng)
        rows.append(_record(i, "pathological", "drop_and_disorder", p))
        i += 1

    # boundary empty
    rows.append(_record(i, "pathological", "empty", []))
    i += 1

    return rows


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "golden" / CASE
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    rows = build_dataset()
    for row in rows:
        (out / f"{row['id']}.json").write_text(_canonical_dump(row), encoding="utf-8")
    pathological = sum(1 for r in rows if r["category"] == "pathological")
    ratio = pathological / len(rows)
    print(f"wrote {len(rows)} records to {out} (pathological_ratio={ratio:.2%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
