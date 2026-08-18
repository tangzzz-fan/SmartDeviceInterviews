"""
生成 HRV 频域 golden（含中间快照）。

只允许本脚本写出 expected/snapshots——禁止用 C/Swift 结果回写。
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from .hrv_freq_prototype import HRVFreqInputError, hrv_freq_domain

SEED = 42
CASE = "hrv_freq_domain"


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
        "generator": "python/hrv_freq_prototype.py",
        "source": "synthetic",
        "license_note": "synthetic internal",
    }
    serializable_rr = [0.0 if (isinstance(x, float) and not math.isfinite(x)) else x for x in rr]
    base: dict[str, Any] = {
        "id": f"hrv_fd_{idx:03d}",
        "case": CASE,
        "category": category,
        "pathology": pathology,
        "input": {"rr_ms": serializable_rr, "non_finite_mode": non_finite_mode},
        "meta": meta,
    }
    try:
        out = hrv_freq_domain(rr)
        snaps = out["snapshots"]
        base["expected"] = {
            "lf": out["lf"],
            "hf": out["hf"],
            "lf_hf_ratio": out["lf_hf_ratio"],
            "ok": True,
            "error": None,
        }
        # 中间快照：逐环定位漂移（本 case 灵魂）
        base["snapshots"] = {
            "resampled": snaps["resampled"],
            "detrended": snaps["detrended"],
            "windowed": snaps["windowed"],
            "psd": snaps["psd"],
            "freqs": snaps["freqs"],
        }
    except HRVFreqInputError as exc:
        base["expected"] = {
            "lf": None,
            "hf": None,
            "lf_hf_ratio": None,
            "ok": False,
            "error": exc.code,
        }
        base["snapshots"] = {}
    return base


def _synth_rr(rng: random.Random, length: int = 40, center: float = 800.0) -> list[float]:
    # 轻微正弦调制 + 噪声，保证去趋势后仍有频域能量
    out: list[float] = []
    for i in range(length):
        mod = 40.0 * math.sin(2.0 * math.pi * i / 12.0)  # ~呼吸相关波动
        out.append(center + mod + rng.uniform(-15.0, 15.0))
    return out


def build_dataset() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []
    i = 1

    for _ in range(22):
        rows.append(_record(i, "normal", "none", _synth_rr(rng, 40)))
        i += 1

    # 边界：刚好 16 个；较长序列
    rows.append(_record(i, "boundary", "none", _synth_rr(rng, 16)))
    i += 1
    rows.append(_record(i, "boundary", "none", _synth_rr(rng, 80, center=750.0)))
    i += 1
    rows.append(_record(i, "boundary", "none", _synth_rr(rng, 24, center=900.0)))
    i += 1

    # 病态
    rows.append(_record(i, "pathological", "empty", []))
    i += 1
    rows.append(_record(i, "pathological", "too_short", [800.0] * 8))
    i += 1
    rows.append(_record(i, "pathological", "too_short", [800.0] * 15))
    i += 1
    rows.append(
        _record(
            i,
            "pathological",
            "non_finite",
            [800.0 if j != 1 else float("nan") for j in range(20)],
            non_finite_mode="nan_at_1",
        )
    )
    i += 1
    rows.append(
        _record(
            i,
            "pathological",
            "non_finite",
            [800.0 if j != 1 else float("inf") for j in range(20)],
            non_finite_mode="inf_at_1",
        )
    )
    i += 1
    # 常数 RR → 去趋势后全 0 → HF=0 → invalid_arg
    rows.append(_record(i, "pathological", "zero_power", [800.0] * 30))
    i += 1

    for _ in range(8):
        rr = _synth_rr(rng, 35)
        rr[10] = 1600.0
        rows.append(_record(i, "pathological", "missing_beat", rr))
        i += 1

    for _ in range(8):
        rr = _synth_rr(rng, 35)
        rr[12] = 320.0
        rows.append(_record(i, "pathological", "ectopic", rr))
        i += 1

    for _ in range(6):
        rr = [rng.uniform(400.0, 1200.0) for _ in range(40)]
        rows.append(_record(i, "pathological", "extreme_noise", rr))
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
