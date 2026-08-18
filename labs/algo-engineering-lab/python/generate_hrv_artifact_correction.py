"""
生成 HRV 伪差校正 golden JSON。
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from .hrv_artifact_prototype import correct_artifacts
from .hrv_prototype import HRVInputError

SEED = 42
CASE = "hrv_artifact_correction"


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _record(
    idx: int,
    category: str,
    pathology: str,
    rr: list[float],
    *,
    non_finite_mode: str | None = None,
) -> dict[str, Any]:
    meta = {
        "seed": SEED,
        "generator": "python/hrv_artifact_prototype.py",
        "source": "synthetic",
        "license_note": "synthetic internal",
    }
    serializable_rr = [0.0 if (isinstance(x, float) and not math.isfinite(x)) else x for x in rr]
    base: dict[str, Any] = {
        "id": f"hrv_ac_{idx:03d}",
        "case": CASE,
        "category": category,
        "pathology": pathology,
        "input": {"rr_ms": serializable_rr, "non_finite_mode": non_finite_mode},
        "meta": meta,
    }
    try:
        out = correct_artifacts(rr)
        base["expected"] = {
            "sdnn_ms": out["sdnn_ms"],
            "rmssd_ms": out["rmssd_ms"],
            "pnn50": out["pnn50"],
            "ok": True,
            "error": None,
        }
        base["snapshots"] = {
            "rr_raw": out["rr_raw"],
            "artifact_mask": out["artifact_mask"],
            "rr_corrected": out["rr_corrected"],
            "mean_rr_ms": out["mean_rr_ms"],
        }
    except HRVInputError as exc:
        base["expected"] = {
            "sdnn_ms": None,
            "rmssd_ms": None,
            "pnn50": None,
            "ok": False,
            "error": exc.code,
        }
        base["snapshots"] = {}
    return base


def _synth_normal(rng: random.Random, length: int = 40) -> list[float]:
    return [800.0 + rng.uniform(-25.0, 25.0) for _ in range(length)]


def build_dataset() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []
    i = 1

    for _ in range(22):
        rows.append(_record(i, "normal", "none", _synth_normal(rng)))
        i += 1

    rows.append(_record(i, "boundary", "constant", [800.0, 800.0, 800.0]))
    i += 1
    rows.append(_record(i, "boundary", "short_valid", [760.0, 800.0, 820.0, 790.0]))
    i += 1

    rows.append(_record(i, "pathological", "empty", []))
    i += 1
    rows.append(_record(i, "pathological", "single", [800.0]))
    i += 1
    rows.append(_record(i, "pathological", "non_finite", [800.0, float("nan"), 820.0], non_finite_mode="nan_at_1"))
    i += 1
    rows.append(_record(i, "pathological", "non_finite", [800.0, float("inf"), 820.0], non_finite_mode="inf_at_1"))
    i += 1

    for _ in range(10):
        rr = _synth_normal(rng, 30)
        rr[10] = 1600.0
        rows.append(_record(i, "pathological", "missing_beat", rr))
        i += 1
    for _ in range(10):
        rr = _synth_normal(rng, 30)
        rr[12] = 320.0
        rows.append(_record(i, "pathological", "ectopic", rr))
        i += 1
    for _ in range(8):
        rr = _synth_normal(rng, 35)
        rr[8] = 250.0
        rr[9] = 2100.0
        rows.append(_record(i, "pathological", "consecutive_outliers", rr))
        i += 1
    return rows


def write_golden(out_dir: Path) -> tuple[int, float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    rows = build_dataset()
    for row in rows:
        (out_dir / f"{row['id']}.json").write_text(_canonical_dump(row), encoding="utf-8")
    pathological = sum(1 for r in rows if r["category"] == "pathological")
    return len(rows), pathological / len(rows)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "golden" / CASE
    n, ratio = write_golden(out)
    print(f"wrote {n} records to {out} (pathological_ratio={ratio:.2%})")
    if ratio < 0.40:
        print("ERROR: pathological ratio < 40%")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
