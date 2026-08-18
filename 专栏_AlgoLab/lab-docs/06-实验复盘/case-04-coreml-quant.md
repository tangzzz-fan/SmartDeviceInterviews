# Case04 实验复盘：CoreML FP32 vs FP16 量化漂移

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

> **零基础请先读：** [`docs/09-CoreML入门/00-导读.md`](../09-CoreML入门/00-导读.md)。

---

## 1. 假设

- FP16 不是「精度减半」；应看 **top-1 一致率** 与 **置信度分布偏移**。
- 预处理均值/方差若 App 与模型各做一半，会制造「量化无辜背锅」的假事故。

## 2. 做法

- 合成 rest/walk/run 特征 → `StandardScaler`（单源）→ `MLPClassifier` 权重导出 MIL → `coremltools` 分别转 FLOAT32 / FLOAT16。
- 树模型（GBM）在 coremltools 9 下无法走 `compute_precision` 的 mlprogram 路径，故改为 MLP→MIL（记入对齐口径已知差异）。

## 3. 数字

| 指标 | 阈值 | 实测 | 环境 |
| :--- | :--- | :--- | :--- |
| top-1 一致率 FP16↔FP32 | ≥95% | **100%**（val=200） | macOS arm64 · coremltools 9.0 · `uv run` |
| 置信度偏移均值 | abs ≤0.05 | ~1e-5 | 同上 |
| sklearn↔FP32 top-1 | — | 100% | 同上 |
| val accuracy | — | 94.5% | 合成数据，仅作 sanity |

重跑：`uv sync --extra ml && uv run python -m python.generate_golden coreml_quant`

## 4. 坑

- `scikit-learn>=1.6` 会被 coremltools 禁用转换 API → 锁 `<1.6`。
- GBM/树转换停在 `pipelineClassifier`，不能演示 FLOAT16 compute_precision。
- Swift 关键字 `case` 不能直接作 Decodable 字段名。

## 5. 结论

**上端后先看一致率与置信度分布；预处理必须单源。**

## 6. 面试卡片（≤5）

- 我不盯单样本 logits，盯验证集 top-1 一致率和置信度分布。
- 预处理均值方差要么全烘进模型，要么全在 App，禁止各做一半。
- FP16 漂移要用产品语义指标验收，不是 1e-12 逐点误差。
- 转换链路选得动 `compute_precision` 的路径（本 lab：MIL mlprogram）。
- 本仓库是验证性原型，不是生产睡眠/运动模型。
