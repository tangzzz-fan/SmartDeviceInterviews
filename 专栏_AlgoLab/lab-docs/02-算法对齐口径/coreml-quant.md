# 对齐口径：CoreML 量化漂移（FP32 vs FP16）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

> **零基础请先读：** [`docs/09-CoreML入门/00-导读.md`](../09-CoreML入门/00-导读.md)（尤其 `01` / `02` / `04`）。  
> Case4。验证性原型，**不是**生产睡眠/运动模型。关注点：量化后看 **top-1 一致率** 与 **置信度分布**，不是逐点 logits 误差。

---

## 1. 环节分解表

| 环节 | 参数 | 取值 | Python | iOS / CoreML |
| :--- | :--- | :--- | :--- | :--- |
| 任务 | — | 三分类活动：`rest` / `walk` / `run`（合成特征） | sklearn `MLPClassifier` 权重 → MIL 小网络 | 同权重导出的 mlprogram |
| 特征 | dim | **8** 维 float；预处理 **单源在训练侧完成**（App 侧只喂已归一化向量） | `StandardScaler` 拟合写入报告 | 输入已是 scaled |
| 数据 | N | train 600 / val 200；`seed=42` | 合成 | — |
| 转换 | FP32 | `ct.convert(mil, compute_precision=FLOAT32)` | coremltools 9.x | `.mlpackage` |
| 转换 | FP16 | `compute_precision=FLOAT16` | 同上 | 同结构另一包 |
| 评估 | — | 同一 val 集；比较 top-1 与 max-softmax 置信度 | `MLModel.predict` | 本 lab 以 Python CoreML runtime 为主 |

---

## 2. 指标与阈值

| 指标 | 定义 | 阈值（lab） | 依据 |
| :--- | :--- | :--- | :--- |
| top-1 一致率 | FP16 与 FP32 预测类相同的比例 | ≥ **95%** | 产品上分类翻转才有意义；ULP 级 logits 差可接受 |
| 置信度偏移 | \(\Delta = p_{\mathrm{fp16}}-p_{\mathrm{fp32}}\)（各自 top-1 概率）均值/标准差 | 报告即可；均值 abs ≤ **0.05** 为绿 | 置信度用于阈值展示时需防「虚高/虚低」 |
| 预处理 | 均值/方差 | **只在训练流水线**；禁止 App 再 normalize 一次 | 混用是线上事故高发区 |

---

## 3. 产物路径

| 产物 | 路径 |
| :--- | :--- |
| FP32 模型 | `artifacts/coreml/activity_fp32.mlpackage` |
| FP16 模型 | `artifacts/coreml/activity_fp16.mlpackage` |
| 对比报告 JSON | `golden/coreml_quant/compare_report.json` |
| 人类可读报告 | `docs/06-实验复盘/case-04-coreml-quant.md` |

> `artifacts/` 可较大；`.mlpackage` 入库以便复现。若体积过大可只入库报告 + 重生脚本。

## 4. 排查手册（出问题怎么查）

### 4.1 top-1 一致率不达标（< 95%）

| 检查项 | 怎么做 |
| :--- | :--- |
| 是否预处理做了两次 | 检查 App 侧是否对已 scaled 的向量又做了 normalize → 直接把问题归到 T15 |
| scaler 参数是否同源 | 对比训练侧报告 vs App 侧实际使用的 mean/scale |
| 模型是否被覆写 | T15 生成器会覆写 `activity_fp32.mlpackage`；若改过训练超参，需要同步重生 |
| 是否在边界决策点集中 | 看验证集里不一致的样本——若两类概率差 < 0.01，则 FP16 翻转可接受 |
| coremltools 版本 | 不同版本 FP16 策略可能不同；锁定 `coremltools==9.x` |

### 4.2 置信度偏移异常

| 检查项 | 怎么做 |
| :--- | :--- |
| 偏移是系统性还是个别样本 | 看 `confidence_hist` 直方图，而非只看均值 |
| 是否超大 logits | FP16 最大值 ~65504；检查模型输出是否有 inf/NaN |
| 是否 softmax 精度损失 | FP16 下 exp() 在大 logits 时易溢出 |

### 4.3 模型加载 / 转换失败

| 检查项 | 怎么做 |
| :--- | :--- |
| `scikit-learn` 版本 | 必须 `< 1.6`，否则 coremltools 禁用转换 API |
| `.mlpackage` 目录完整 | 需含 `Manifest.json` + `Data/com.apple.CoreML/` |
| 用了 `convert_to="neuralnetwork"` | 树模型会走这条路 → 没有 `compute_precision` |

---

## 5. 已知差异

| 差异点 | 量级 | 接受理由 | 确认人 |
| :--- | :--- | :--- | :--- |
| 树模型（GBM）→ mlprogram FLOAT16 | 不可用 | coremltools 9 + sklearn 树转换停在 pipelineClassifier，无法走 compute_precision；改用 MLP 权重进 MIL | lab |
| 合成数据非真实 PPG/IMU | 大 | 练工程口径，非临床精度 | lab |
| 评估在 Mac CoreML，非 Neural Engine 专项 | 中 | 量化一致率优先；ANE 耗时另开 bench | lab |

---

## 5. 面试金句

> 模型上端后我不看单样本精度，看全量验证集的 top-1 一致率和置信度分布。预处理参数必须单源——要么全烘进模型，要么全在 App 侧，绝不能两边各做一半。
