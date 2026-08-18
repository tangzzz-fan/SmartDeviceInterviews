"""
T15：同权活动分类 — App 侧 StandardScaler vs 烘进 CoreML 的预处理对照。

- activity_fp32.mlpackage：吃 scaled 特征（Case04）
- activity_fp32_with_preprocess.mlpackage：吃 raw，图内做 (x-mean)/scale
- 负例：双重 normalize 后喂 App 侧模型，应与正确路径显著偏离
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import coremltools as ct
import numpy as np
from coremltools.converters.mil import Builder as mb
from coremltools.converters.mil.mil import types as mil_types
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from .generate_coreml_quant import (
    HIDDEN,
    N_FEATURES,
    SEED,
    _build_mil_program,
    _output_key,
    _predict_batch,
    _repo_root,
    _synth_dataset,
)


def _build_mil_with_preprocess(
    mean: np.ndarray,
    scale: np.ndarray,
    W1: np.ndarray,
    b1: np.ndarray,
    W2: np.ndarray,
    b2: np.ndarray,
):
    """raw → StandardScaler（对角 linear）→ MLP → softmax。"""
    inv = (1.0 / scale).astype(np.float32)
    # linear: y = x @ W.T + b；要做逐维 (x-m)/s ≡ x*(1/s) + (-m/s)
    W_s = np.diag(inv).astype(np.float32)  # (8, 8) → MIL weight (n_out, n_in)
    b_s = (-mean * inv).astype(np.float32)

    @mb.program(input_specs=[mb.TensorSpec(shape=(1, N_FEATURES), dtype=mil_types.fp32)])
    def prog(raw_features):  # noqa: ANN001
        x = mb.linear(x=raw_features, weight=W_s, bias=b_s)
        h = mb.linear(x=x, weight=W1.astype(np.float32), bias=b1.astype(np.float32))
        h = mb.relu(x=h)
        logits = mb.linear(x=h, weight=W2.astype(np.float32), bias=b2.astype(np.float32))
        probs = mb.softmax(x=logits, axis=-1)
        return probs

    return prog


def run() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    X_all, y_all = _synth_dataset(rng, 800)
    X_train, y_train = X_all[:600], y_all[:600]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)

    mlp = MLPClassifier(
        hidden_layer_sizes=(HIDDEN,),
        activation="relu",
        solver="adam",
        max_iter=800,
        random_state=SEED,
    )
    mlp.fit(X_train_s, y_train)

    W1 = mlp.coefs_[0].T.copy()
    b1 = mlp.intercepts_[0].copy()
    W2 = mlp.coefs_[1].T.copy()
    b2 = mlp.intercepts_[1].copy()

    mean = scaler.mean_.astype(np.float64)
    scale = scaler.scale_.astype(np.float64)

    artifacts = _repo_root() / "artifacts" / "coreml"
    artifacts.mkdir(parents=True, exist_ok=True)
    path_app = artifacts / "activity_fp32.mlpackage"
    path_in = artifacts / "activity_fp32_with_preprocess.mlpackage"

    # App 侧模型（与 Case04 同结构；同 seed 重训权重一致）
    prog_app = _build_mil_program(W1, b1, W2, b2)
    model_app = ct.convert(
        prog_app,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT32,
        inputs=[ct.TensorType(name="features", shape=(1, N_FEATURES))],
    )
    model_app.save(str(path_app))

    prog_in = _build_mil_with_preprocess(mean, scale, W1, b1, W2, b2)
    model_in = ct.convert(
        prog_in,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT32,
        inputs=[ct.TensorType(name="raw_features", shape=(1, N_FEATURES))],
        # 若 convert 忽略 name，仍靠 shape 对齐；predict 用 spec 输出键
    )
    model_in.save(str(path_in))

    # 固定 raw 向量
    raw = np.array(
        [
            [0.10, -0.20, 0.30, 0.10, -0.10, 0.20, 0.00, 0.05],
            [1.80, 1.10, 0.90, 0.60, 0.30, 0.25, 0.10, 0.15],
            [2.60, 2.10, 1.60, 1.20, 0.90, 0.65, 0.50, 0.35],
        ],
        dtype=np.float64,
    )
    scaled = (raw - mean) / scale
    double_scaled = (scaled - mean) / scale  # 负例：再套一次训练集 scaler

    key_app = _output_key(model_app)
    key_in = _output_key(model_in)

    # App 路径：显式 scale 后喂 features
    probs_app = _predict_batch(model_app, scaled, key_app)
    # 入模路径：raw 直接喂（输入名可能是 raw_features）
    probs_in = []
    in_name = model_in.get_spec().description.input[0].name
    for i in range(raw.shape[0]):
        out = model_in.predict({in_name: raw[i : i + 1].astype(np.float32)})
        probs_in.append(np.asarray(out[key_in], dtype=np.float64).reshape(-1))
    probs_in = np.stack(probs_in, axis=0)

    probs_double = _predict_batch(model_app, double_scaled, key_app)

    abs_diff = np.abs(probs_app - probs_in)
    max_abs = float(np.max(abs_diff))
    double_diff = np.abs(probs_double - probs_app)
    double_max = float(np.max(double_diff))

    report: dict[str, Any] = {
        "case": "coreml_preprocess_inmodel",
        "seed": SEED,
        "models": {
            "app_side_scaled": str(path_app.relative_to(_repo_root())),
            "in_model_preprocess": str(path_in.relative_to(_repo_root())),
        },
        "preprocess": {
            "mean": mean.tolist(),
            "scale": scale.tolist(),
        },
        "verification_vectors": {
            "raw_features": raw.tolist(),
            "scaled_features": scaled.tolist(),
            "double_scaled_features": double_scaled.tolist(),
            "expected_probs_app_side": probs_app.tolist(),
            "expected_probs_in_model": probs_in.tolist(),
            "expected_probs_double_normalize_wrong": probs_double.tolist(),
            "tolerance_abs": 1e-5,
            "double_normalize_min_max_abs_diff": 0.01,
        },
        "metrics": {
            "app_vs_inmodel_max_abs_diff": max_abs,
            "double_vs_correct_max_abs_diff": double_max,
        },
        "pass": {
            "app_matches_inmodel": max_abs <= 1e-5,
            "double_normalize_diverges": double_max >= 0.01,
        },
        "disclaimer": "验证性原型：演示预处理单源两种合法落地，及双重 normalize 事故",
    }
    return report


def main() -> int:
    report = run()
    out_dir = _repo_root() / "golden" / "coreml_preprocess_inmodel"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "compare_report.json"
    out_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["metrics"], indent=2))
    print(f"wrote {out_path}")
    if not (report["pass"]["app_matches_inmodel"] and report["pass"]["double_normalize_diverges"]):
        print("ERROR: thresholds not met")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
