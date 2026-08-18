"""
Case4：合成活动三分类 → 小 MLP → CoreML FP32/FP16 → top-1 / 置信度对比。

预处理（StandardScaler）在训练侧完成并写入报告；推理输入为已归一化向量（单源）。
验证性原型，非生产模型。
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

SEED = 42
N_FEATURES = 8
CLASS_NAMES = ["rest", "walk", "run"]
HIDDEN = 16


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _synth_dataset(
    rng: np.random.Generator, n: int
) -> tuple[np.ndarray, np.ndarray]:
    """合成 8 维特征：三类围绕不同中心，模拟粗粒度活动可分性。"""
    centers = np.array(
        [
            [0.0, 0.0, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0],  # rest：低运动能量
            [1.5, 1.2, 0.8, 0.5, 0.3, 0.2, 0.1, 0.1],  # walk
            [2.5, 2.0, 1.5, 1.2, 0.8, 0.6, 0.4, 0.3],  # run
        ],
        dtype=np.float64,
    )
    y = rng.integers(0, 3, size=n)
    X = centers[y] + rng.normal(scale=0.45, size=(n, N_FEATURES))
    return X, y


def _build_mil_program(W1: np.ndarray, b1: np.ndarray, W2: np.ndarray, b2: np.ndarray):
    """
    sklearn MLP: (n_in, n_hid) / (n_hid, n_out)
    MIL linear weight: (n_out, n_in)
    """

    @mb.program(input_specs=[mb.TensorSpec(shape=(1, N_FEATURES), dtype=mil_types.fp32)])
    def prog(features):  # noqa: ANN001 — MIL builder 签名
        h = mb.linear(x=features, weight=W1.astype(np.float32), bias=b1.astype(np.float32))
        h = mb.relu(x=h)
        logits = mb.linear(x=h, weight=W2.astype(np.float32), bias=b2.astype(np.float32))
        probs = mb.softmax(x=logits, axis=-1)
        return probs

    return prog


def _predict_batch(model: ct.models.MLModel, X: np.ndarray, out_key: str) -> np.ndarray:
    probs = []
    for i in range(X.shape[0]):
        row = X[i : i + 1].astype(np.float32)
        out = model.predict({"features": row})
        probs.append(np.asarray(out[out_key], dtype=np.float64).reshape(-1))
    return np.stack(probs, axis=0)


def _output_key(model: ct.models.MLModel) -> str:
    spec = model.get_spec()
    return spec.description.output[0].name


def run() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    X_all, y_all = _synth_dataset(rng, 800)
    X_train, y_train = X_all[:600], y_all[:600]
    X_val, y_val = X_all[600:], y_all[600:]

    # 预处理单源：均值/方差只在这里拟合，推理喂 scaled 向量
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)

    mlp = MLPClassifier(
        hidden_layer_sizes=(HIDDEN,),
        activation="relu",
        solver="adam",
        max_iter=800,
        random_state=SEED,
    )
    mlp.fit(X_train_s, y_train)

    # sklearn: coefs_[0]=(n_in,hid), coefs_[1]=(hid,n_out)
    W1 = mlp.coefs_[0].T.copy()
    b1 = mlp.intercepts_[0].copy()
    W2 = mlp.coefs_[1].T.copy()
    b2 = mlp.intercepts_[1].copy()

    prog = _build_mil_program(W1, b1, W2, b2)

    artifacts = _repo_root() / "artifacts" / "coreml"
    artifacts.mkdir(parents=True, exist_ok=True)
    path_fp32 = artifacts / "activity_fp32.mlpackage"
    path_fp16 = artifacts / "activity_fp16.mlpackage"

    model_fp32 = ct.convert(
        prog,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT32,
        inputs=[ct.TensorType(name="features", shape=(1, N_FEATURES))],
    )
    model_fp16 = ct.convert(
        prog,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT16,
        inputs=[ct.TensorType(name="features", shape=(1, N_FEATURES))],
    )
    model_fp32.save(str(path_fp32))
    model_fp16.save(str(path_fp16))

    key32 = _output_key(model_fp32)
    key16 = _output_key(model_fp16)
    p32 = _predict_batch(model_fp32, X_val_s, key32)
    p16 = _predict_batch(model_fp16, X_val_s, key16)

    pred32 = np.argmax(p32, axis=1)
    pred16 = np.argmax(p16, axis=1)
    top1_agree = float(np.mean(pred32 == pred16))

    conf32 = p32[np.arange(len(pred32)), pred32]
    conf16 = p16[np.arange(len(pred16)), pred16]
    delta = conf16 - conf32
    conf_shift_mean = float(np.mean(delta))
    conf_shift_std = float(np.std(delta))

    # 相对 sklearn 参考（非必须，但证明权重导出正确）
    sk_pred = mlp.predict(X_val_s)
    sk_agree_fp32 = float(np.mean(sk_pred == pred32))

    report: dict[str, Any] = {
        "case": "coreml_quant",
        "seed": SEED,
        "n_val": int(len(y_val)),
        "class_names": CLASS_NAMES,
        "preprocess": {
            "kind": "StandardScaler",
            "single_source": "train_pipeline_only",
            "mean": scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
            "note": "App 侧禁止再 normalize；喂入已是 scaled 特征",
        },
        "models": {
            "fp32": str(path_fp32.relative_to(_repo_root())),
            "fp16": str(path_fp16.relative_to(_repo_root())),
            "coremltools": ct.__version__,
        },
        "metrics": {
            "top1_agreement_fp16_vs_fp32": top1_agree,
            "confidence_shift_mean": conf_shift_mean,
            "confidence_shift_std": conf_shift_std,
            "sklearn_vs_fp32_top1": sk_agree_fp32,
            "fp32_val_accuracy": float(np.mean(pred32 == y_val)),
            "fp16_val_accuracy": float(np.mean(pred16 == y_val)),
        },
        "thresholds": {
            "top1_agreement_min": 0.95,
            "confidence_shift_mean_abs_max": 0.05,
        },
        "pass": {
            "top1": top1_agree >= 0.95,
            "conf_shift": abs(conf_shift_mean) <= 0.05,
        },
        "disclaimer": "验证性原型，非生产健康/睡眠模型",
    }

    # 固定向量回归样本：用于 Swift 侧直接加载 .mlpackage 后逐值对齐
    verification_raw = np.array(
        [
            [0.10, -0.20, 0.30, 0.10, -0.10, 0.20, 0.00, 0.05],
            [1.80, 1.10, 0.90, 0.60, 0.30, 0.25, 0.10, 0.15],
            [2.60, 2.10, 1.60, 1.20, 0.90, 0.65, 0.50, 0.35],
        ],
        dtype=np.float64,
    )
    verification_scaled = (verification_raw - scaler.mean_) / scaler.scale_
    v32 = _predict_batch(model_fp32, verification_scaled, key32)
    v16 = _predict_batch(model_fp16, verification_scaled, key16)
    report["verification_vectors"] = {
        "raw_features": verification_raw.tolist(),
        "scaled_features": verification_scaled.tolist(),
        "expected_probs_fp32": v32.tolist(),
        "expected_probs_fp16": v16.tolist(),
        # Swift 侧对齐阈值：fp32 用更严格容差，fp16 略放宽
        "tolerance_fp32_abs": 1e-6,
        "tolerance_fp16_abs": 5e-4,
    }

    # 直方图分箱（置信度分布偏移的可读摘要）
    bins = [round(x, 2) for x in np.linspace(0.0, 1.0, 11).tolist()]
    hist32, _ = np.histogram(conf32, bins=bins)
    hist16, _ = np.histogram(conf16, bins=bins)
    report["confidence_hist"] = {
        "bins": bins,
        "fp32": hist32.tolist(),
        "fp16": hist16.tolist(),
    }
    return report


def main() -> int:
    report = run()
    out_dir = _repo_root() / "golden" / "coreml_quant"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "compare_report.json"
    out_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["metrics"], indent=2))
    print(f"wrote {out_path}")
    if not (report["pass"]["top1"] and report["pass"]["conf_shift"]):
        print("ERROR: thresholds not met")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
