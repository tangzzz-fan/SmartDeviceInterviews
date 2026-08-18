"""
CoreML 输入分布漂移监控参考实现（Python = 真值）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import coremltools as ct
import numpy as np

from .generate_coreml_quant import run as run_coreml_quant

SEED = 42
N_FEATURES = 8


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_model_and_preprocess() -> tuple[ct.models.MLModel, np.ndarray, np.ndarray]:
    """若 T5 模型/报告缺失，自动重生，保证 T11 可独立运行。"""
    report_path = _repo_root() / "golden" / "coreml_quant" / "compare_report.json"
    model_path = _repo_root() / "artifacts" / "coreml" / "activity_fp32.mlpackage"
    if not report_path.exists() or not model_path.exists():
        run_coreml_quant()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    mean = np.asarray(report["preprocess"]["mean"], dtype=np.float64)
    scale = np.asarray(report["preprocess"]["scale"], dtype=np.float64)
    model = ct.models.MLModel(str(model_path))
    return model, mean, scale


def _synth_features(rng: np.random.Generator, n: int, *, shifted: bool) -> np.ndarray:
    """与 T5 同维度的合成特征；shifted=True 注入明显分布偏移。"""
    X = rng.normal(loc=0.0, scale=1.0, size=(n, N_FEATURES))
    if shifted:
        X[:, 0] += 1.8
        X[:, 1] += 1.2
        X[:, 4] *= 1.8
    return X


def _predict_probs(model: ct.models.MLModel, X_scaled: np.ndarray) -> np.ndarray:
    out_key = model.get_spec().description.output[0].name
    probs = []
    for i in range(X_scaled.shape[0]):
        out = model.predict({"features": X_scaled[i : i + 1].astype(np.float32)})
        probs.append(np.asarray(out[out_key], dtype=np.float64).reshape(-1))
    return np.stack(probs, axis=0)


def _hist_bins(ref: np.ndarray, cur: np.ndarray, bins: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    edges = np.histogram_bin_edges(np.concatenate([ref, cur]), bins=bins)
    ref_hist, _ = np.histogram(ref, bins=edges)
    cur_hist, _ = np.histogram(cur, bins=edges)
    return ref_hist.astype(np.float64), cur_hist.astype(np.float64), edges


def _psi(ref: np.ndarray, cur: np.ndarray, bins: int = 10) -> float:
    ref_hist, cur_hist, _ = _hist_bins(ref, cur, bins=bins)
    ref_p = ref_hist / max(ref_hist.sum(), 1.0)
    cur_p = cur_hist / max(cur_hist.sum(), 1.0)
    eps = 1e-8
    ref_p = np.clip(ref_p, eps, 1.0)
    cur_p = np.clip(cur_p, eps, 1.0)
    return float(np.sum((cur_p - ref_p) * np.log(cur_p / ref_p)))


def _kl(ref: np.ndarray, cur: np.ndarray, bins: int = 10) -> float:
    ref_hist, cur_hist, _ = _hist_bins(ref, cur, bins=bins)
    ref_p = ref_hist / max(ref_hist.sum(), 1.0)
    cur_p = cur_hist / max(cur_hist.sum(), 1.0)
    eps = 1e-8
    ref_p = np.clip(ref_p, eps, 1.0)
    cur_p = np.clip(cur_p, eps, 1.0)
    return float(np.sum(cur_p * np.log(cur_p / ref_p)))


def _alert_level(max_psi: float, kl_conf: float) -> str:
    if max_psi >= 0.25 or kl_conf >= 0.20:
        return "high"
    if max_psi >= 0.10 or kl_conf >= 0.08:
        return "medium"
    return "low"


def run() -> dict[str, Any]:
    model, mean, scale = _ensure_model_and_preprocess()
    rng = np.random.default_rng(SEED)

    baseline_raw = _synth_features(rng, 600, shifted=False)
    shifted_raw = _synth_features(rng, 600, shifted=True)
    stable_raw = _synth_features(rng, 600, shifted=False)

    baseline = (baseline_raw - mean) / scale
    shifted = (shifted_raw - mean) / scale
    stable = (stable_raw - mean) / scale

    base_probs = _predict_probs(model, baseline)
    shifted_probs = _predict_probs(model, shifted)
    stable_probs = _predict_probs(model, stable)

    feature_psi_shifted = [_psi(baseline[:, i], shifted[:, i]) for i in range(N_FEATURES)]
    feature_psi_stable = [_psi(baseline[:, i], stable[:, i]) for i in range(N_FEATURES)]

    conf_base = np.max(base_probs, axis=1)
    conf_shifted = np.max(shifted_probs, axis=1)
    conf_stable = np.max(stable_probs, axis=1)
    kl_shifted = _kl(conf_base, conf_shifted)
    kl_stable = _kl(conf_base, conf_stable)

    max_psi_shifted = float(max(feature_psi_shifted))
    max_psi_stable = float(max(feature_psi_stable))

    level_shifted = _alert_level(max_psi_shifted, kl_shifted)
    level_stable = _alert_level(max_psi_stable, kl_stable)

    thresholds = {
        "psi_medium": 0.10,
        "psi_high": 0.25,
        "kl_medium": 0.08,
        "kl_high": 0.20,
    }
    return {
        "case": "coreml_drift_monitoring",
        "seed": SEED,
        "n_samples": 600,
        "thresholds": thresholds,
        "stable": {
            "feature_psi": feature_psi_stable,
            "max_psi": max_psi_stable,
            "kl_confidence": kl_stable,
            "alert_level": level_stable,
        },
        "shifted": {
            "feature_psi": feature_psi_shifted,
            "max_psi": max_psi_shifted,
            "kl_confidence": kl_shifted,
            "alert_level": level_shifted,
        },
        "pass": {
            "stable_low_alert": level_stable == "low",
            "shifted_not_low": level_shifted in ("medium", "high"),
            "shifted_more_than_stable": (max_psi_shifted > max_psi_stable) and (kl_shifted > kl_stable),
        },
        "disclaimer": "验证性原型，非生产监控规则",
    }
