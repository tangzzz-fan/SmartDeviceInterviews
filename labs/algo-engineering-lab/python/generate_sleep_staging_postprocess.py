"""
生成睡眠分期后处理 golden。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .sleep_staging_postprocess_prototype import postprocess

SEED = 42
CASE = "sleep_staging_postprocess"


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _one_hot(stage_idx: int, noise: float, rng: random.Random) -> list[float]:
    vals = [noise * rng.random() for _ in range(5)]
    vals[stage_idx] += 1.0
    s = sum(vals)
    return [v / s for v in vals]


def _record(i: int, category: str, pathology: str, probs: list[list[float]]) -> dict[str, Any]:
    out = postprocess(probs)
    return {
        "id": f"ssp_{i:03d}",
        "case": CASE,
        "category": category,
        "pathology": pathology,
        "input": {"epoch_sec": 30, "prob_seq": probs},
        "expected": {
            "raw_stages": out["raw_stages"],
            "smoothed_stages": out["smoothed_stages"],
            "metrics": out["metrics"],
            "ok": True,
        },
        "meta": {"seed": SEED, "generator": "python/sleep_staging_postprocess_prototype.py"},
    }


def build_dataset() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []
    i = 1

    # 正常序列：W -> N1 -> N2 -> N3 -> REM -> N2
    base = [0] * 10 + [1] * 4 + [2] * 18 + [3] * 12 + [4] * 10 + [2] * 6
    for _ in range(12):
        probs = [_one_hot(s, noise=0.05, rng=rng) for s in base]
        rows.append(_record(i, "normal", "none", probs))
        i += 1

    # 病态抖动：插入大量单点跳变
    for _ in range(14):
        jitter = base[:]
        for k in range(5, len(jitter), 7):
            jitter[k] = rng.choice([0, 4, 1, 3])
        probs = [_one_hot(s, noise=0.20, rng=rng) for s in jitter]
        rows.append(_record(i, "pathological", "jitter", probs))
        i += 1

    # 病态短序列
    for _ in range(6):
        seq = [0, 1, 0, 2, 0, 4]
        probs = [_one_hot(s, noise=0.25, rng=rng) for s in seq]
        rows.append(_record(i, "pathological", "short_jitter", probs))
        i += 1

    # 边界空
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
