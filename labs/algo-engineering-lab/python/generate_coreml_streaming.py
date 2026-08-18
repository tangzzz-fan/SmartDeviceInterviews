"""
T16：StreamingFIR 滑窗 → 8 维窗特征 → StandardScaler → CoreML 活动分类。

与 Case5 同源因果 FIR；窗特征公式与 Swift `WindowActivityFeatures` 对齐。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import coremltools as ct
import numpy as np

from .generate_coreml_quant import N_FEATURES, SEED, _output_key, _repo_root
from .generate_streaming_fir import PACKET_SIZE, WINDOW, _load_coeffs, causal_fir, packetize, synth_ppg

CASE = "coreml_streaming"
FS = 25.0
N_SAMPLES = 100  # 4 个窗


def _extract_window_features(y: np.ndarray) -> np.ndarray:
    """25 点滤波窗 → 8 维特征（与 Swift 同口径）。"""
    assert y.shape == (WINDOW,)
    mean = float(np.mean(y))
    std = float(np.std(y, ddof=0))
    rng = float(np.max(y) - np.min(y))
    energy = float(np.mean(y * y))
    first = float(y[0])
    last = float(y[-1])
    delta = abs(last - first)
    mid = float(y[WINDOW // 2])
    return np.asarray([mean, std, rng, energy, first, last, delta, mid], dtype=np.float64)


def _load_scaler() -> tuple[np.ndarray, np.ndarray]:
    report_path = _repo_root() / "golden" / "coreml_quant" / "compare_report.json"
    if not report_path.exists():
        from .generate_coreml_quant import run as run_quant

        run_quant()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    mean = np.asarray(report["preprocess"]["mean"], dtype=np.float64)
    scale = np.asarray(report["preprocess"]["scale"], dtype=np.float64)
    return mean, scale


def _ensure_model() -> ct.models.MLModel:
    path = _repo_root() / "artifacts" / "coreml" / "activity_fp32.mlpackage"
    if not path.exists():
        from .generate_coreml_quant import run as run_quant

        run_quant()
    return ct.models.MLModel(str(path))


def run() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    b = np.asarray(_load_coeffs(), dtype=np.float64)
    x = synth_ppg(N_SAMPLES, rng)
    y = causal_fir(x, b)
    assert len(y) % WINDOW == 0

    mean, scale = _load_scaler()
    model = _ensure_model()
    out_key = _output_key(model)
    in_name = model.get_spec().description.input[0].name

    windows = y.reshape(-1, WINDOW)
    features = np.stack([_extract_window_features(w) for w in windows], axis=0)
    scaled = (features - mean) / scale

    probs = []
    for i in range(scaled.shape[0]):
        out = model.predict({in_name: scaled[i : i + 1].astype(np.float32)})
        probs.append(np.asarray(out[out_key], dtype=np.float64).reshape(-1))
    probs_arr = np.stack(probs, axis=0)

    packets = packetize(x.tolist(), packet_size=PACKET_SIZE)

    return {
        "case": CASE,
        "seed": SEED,
        "input": {
            "fs": FS,
            "packet_size": PACKET_SIZE,
            "window": WINDOW,
            "n_samples": N_SAMPLES,
            "packets": packets,
            "gap_policy": "zero_fill",
        },
        "preprocess": {
            "mean": mean.tolist(),
            "scale": scale.tolist(),
            "source": "golden/coreml_quant/compare_report.json",
        },
        "model": "artifacts/coreml/activity_fp32.mlpackage",
        "feature_formula": [
            "mean",
            "std_ddof0",
            "max_minus_min",
            "mean_square",
            "first",
            "last",
            "abs_last_minus_first",
            "mid_sample",
        ],
        "expected": {
            "filtered_y": y.tolist(),
            "window_features": features.tolist(),
            "scaled_features": scaled.tolist(),
            "probs": probs_arr.tolist(),
        },
        "tolerance_probs_abs": 5e-4,
        "tolerance_features_abs": 1e-9,
        "disclaimer": "验证性原型：窗特征为工程演示，非临床活动识别",
    }


def main() -> int:
    report = run()
    out_dir = _repo_root() / "golden" / "coreml_streaming"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stream_report.json"
    out_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"windows={len(report['expected']['probs'])} wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
