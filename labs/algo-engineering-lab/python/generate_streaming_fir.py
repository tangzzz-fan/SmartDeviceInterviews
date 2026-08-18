"""
生成流式 FIR / 丢包场景的参考输出（因果 FIR）。

口径：docs/02-算法对齐口径/streaming-fir.md
系数与 Case2 同源（从 golden/fir_ppg/coeffs.json 读取）。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

SEED = 42
FS = 25.0
CASE = "streaming_fir"
PACKET_SIZE = 2
WINDOW = 25


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _load_coeffs() -> list[float]:
    path = _repo_root() / "golden" / "fir_ppg" / "coeffs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["coeffs"])


def causal_fir(x: np.ndarray, b: np.ndarray) -> np.ndarray:
    """y[n]=sum_k b[k]*x[n-k]，x<0 为 0。"""
    m = len(b)
    y = np.zeros_like(x, dtype=np.float64)
    for n in range(len(x)):
        acc = 0.0
        for k in range(m):
            j = n - k
            if j >= 0:
                acc += b[k] * x[j]
        y[n] = acc
    return y


def synth_ppg(n: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(n, dtype=np.float64) / FS
    # 1.2Hz 心动成分 + 低频漂移 + 噪声
    sig = (
        1.0 * np.sin(2 * math.pi * 1.2 * t)
        + 0.3 * np.sin(2 * math.pi * 0.15 * t)
        + 0.05 * rng.normal(size=n)
    )
    return sig


def packetize(samples: list[float], packet_size: int = PACKET_SIZE) -> list[dict[str, Any]]:
    packets = []
    seq = 0
    for i in range(0, len(samples), packet_size):
        chunk = samples[i : i + packet_size]
        if not chunk:
            break
        packets.append({"seq": seq, "samples": chunk})
        seq += 1
    return packets


def apply_drops(
    packets: list[dict[str, Any]], drop_seqs: set[int]
) -> tuple[list[dict[str, Any]], list[float]]:
    """返回存活包，以及 zero_fill 重建后的连续采样序列。"""
    kept = [p for p in packets if p["seq"] not in drop_seqs]
    rebuilt: list[float] = []
    for p in packets:
        if p["seq"] in drop_seqs:
            rebuilt.extend([0.0] * len(p["samples"]))
        else:
            rebuilt.extend(p["samples"])
    return kept, rebuilt


def build_dataset() -> list[dict[str, Any]]:
    rng = np.random.default_rng(SEED)
    b = np.asarray(_load_coeffs(), dtype=np.float64)
    rows: list[dict[str, Any]] = []

    # 1) 无丢包：整段因果 vs 流式应对齐
    n = 200  # 8 秒
    x = synth_ppg(n, rng)
    y = causal_fir(x, b)
    packets = packetize(x.tolist())
    rows.append(
        {
            "id": "stream_001_continuous",
            "case": CASE,
            "category": "normal",
            "pathology": "none",
            "input": {
                "fs": FS,
                "packet_size": PACKET_SIZE,
                "window": WINDOW,
                "gap_policy": "zero_fill",
                "packets": packets,
                "drop_seqs": [],
            },
            "expected": {
                "y": y.tolist(),
                "ok": True,
            },
            "meta": {"seed": SEED, "generator": "python/generate_streaming_fir.py"},
        }
    )

    # 2) 约 5% 丢包 + zero_fill
    n2 = 200
    x2 = synth_ppg(n2, rng)
    packets2 = packetize(x2.tolist())
    n_drop = max(1, int(round(0.05 * len(packets2))))
    drop_seqs = set(int(i) for i in rng.choice(len(packets2), size=n_drop, replace=False))
    kept, rebuilt = apply_drops(packets2, drop_seqs)
    y2 = causal_fir(np.asarray(rebuilt, dtype=np.float64), b)
    rows.append(
        {
            "id": "stream_002_drop_zero_fill",
            "case": CASE,
            "category": "pathological",
            "pathology": "packet_loss",
            "input": {
                "fs": FS,
                "packet_size": PACKET_SIZE,
                "window": WINDOW,
                "gap_policy": "zero_fill",
                "packets": kept,
                "drop_seqs": sorted(drop_seqs),
                "all_packets_for_rebuild": packets2,
            },
            "expected": {
                "y": y2.tolist(),
                "rebuilt_x": rebuilt,
                "ok": True,
            },
            "meta": {"seed": SEED, "n_drop": n_drop, "generator": "python/generate_streaming_fir.py"},
        }
    )

    # 3) 边界：空包列表
    rows.append(
        {
            "id": "stream_003_empty",
            "case": CASE,
            "category": "pathological",
            "pathology": "empty",
            "input": {
                "fs": FS,
                "packet_size": PACKET_SIZE,
                "window": WINDOW,
                "gap_policy": "zero_fill",
                "packets": [],
                "drop_seqs": [],
            },
            "expected": {"y": [], "ok": True},
            "meta": {"seed": SEED, "generator": "python/generate_streaming_fir.py"},
        }
    )

    return rows


def main() -> int:
    out_dir = _repo_root() / "golden" / CASE
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    rows = build_dataset()
    for row in rows:
        (out_dir / f"{row['id']}.json").write_text(_canonical_dump(row), encoding="utf-8")
    print(f"wrote {len(rows)} records to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
