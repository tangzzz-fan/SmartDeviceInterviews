"""
生成 HRV 时域 golden JSON。

只允许本脚本（及 Python 原型）写出 expected——禁止用 C/Swift 结果回写。
种子固定为 42，保证删除 golden/ 后可逐文件复现。
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

from .hrv_prototype import HRVInputError, hrv_time_domain

SEED = 42
CASE = "hrv_time_domain"


def _canonical_dump(obj: Any) -> str:
    """稳定序列化：排序 key + 紧凑浮点，便于逐字节复现。"""
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
        "generator": "python/hrv_prototype.py",
        "source": "synthetic",
        "license_note": "synthetic internal",
    }
    # JSON 不能编码 NaN/Inf；非有限用例用 finite 占位 + non_finite_mode，测试侧再注入
    serializable_rr = [0.0 if (isinstance(x, float) and not math.isfinite(x)) else x for x in rr]
    base: dict[str, Any] = {
        "id": f"hrv_td_{idx:03d}",
        "case": CASE,
        "category": category,
        "pathology": pathology,
        "input": {"rr_ms": serializable_rr, "non_finite_mode": non_finite_mode},
        "meta": meta,
    }
    try:
        out = hrv_time_domain(rr)
        base["expected"] = {
            "sdnn_ms": out["sdnn_ms"],
            "rmssd_ms": out["rmssd_ms"],
            "pnn50": out["pnn50"],
            "ok": True,
            "error": None,
        }
        base["snapshots"] = {"mean_rr_ms": out["mean_rr_ms"]}
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
    # 围绕 800ms 的轻微波动，模拟安静窦性心律
    return [800.0 + rng.uniform(-30.0, 30.0) for _ in range(length)]


def build_dataset() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    rows: list[dict[str, Any]] = []
    i = 1

    # —— 正常（约 30%）——
    for _ in range(22):
        rows.append(_record(i, "normal", "none", _synth_normal(rng)))
        i += 1

    # —— 边界 ——
    rows.append(_record(i, "boundary", "none", [800.0, 800.0]))  # 常数序列，SDNN=0
    i += 1
    rows.append(_record(i, "boundary", "none", [600.0, 650.0, 700.0]))
    i += 1
    rows.append(_record(i, "boundary", "none", [800.0 + k for k in range(10)]))
    i += 1

    # —— 病态 / 错误路径（≥40%）——
    rows.append(_record(i, "pathological", "empty", []))
    i += 1
    rows.append(_record(i, "pathological", "single", [800.0]))
    i += 1
    rows.append(_record(i, "pathological", "non_finite", [800.0, float("nan"), 820.0], non_finite_mode="nan_at_1"))
    i += 1
    rows.append(_record(i, "pathological", "non_finite", [800.0, float("inf")], non_finite_mode="inf_at_1"))
    i += 1

    # 缺失搏动：人为插入超长 RR（本 case 不做校正，只作为病理输入仍应算出数）
    for _ in range(8):
        rr = _synth_normal(rng, 30)
        rr[10] = 1600.0  # 疑似漏搏
        rows.append(_record(i, "pathological", "missing_beat", rr))
        i += 1

    # 异位：突然极短 RR
    for _ in range(8):
        rr = _synth_normal(rng, 30)
        rr[12] = 320.0
        rows.append(_record(i, "pathological", "ectopic", rr))
        i += 1

    # 极端噪声
    for _ in range(6):
        rr = [rng.uniform(200.0, 1800.0) for _ in range(25)]
        rows.append(_record(i, "pathological", "extreme_noise", rr))
        i += 1

    return rows


def write_golden(out_dir: Path) -> tuple[int, float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    # 清掉旧文件，保证重生与仓库一致
    for old in out_dir.glob("*.json"):
        old.unlink()

    rows = build_dataset()
    for row in rows:
        path = out_dir / f"{row['id']}.json"
        path.write_text(_canonical_dump(row), encoding="utf-8")

    pathological = sum(1 for r in rows if r["category"] == "pathological")
    ratio = pathological / len(rows)
    return len(rows), ratio


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
