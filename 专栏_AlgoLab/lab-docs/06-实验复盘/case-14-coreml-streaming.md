# Case14 实验复盘：CoreML 流式滑窗推理

版本：0.2.0 · 日期：2026-07-29 · 作者：lab · 状态：草稿

> 对齐口径（含排查手册）：[`coreml-streaming.md`](../02-算法对齐口径/coreml-streaming.md)  
> 入门：[`../09-CoreML入门/03-CoreML运行时与硬件.md`](../09-CoreML入门/03-CoreML运行时与硬件.md)

---

## 1. 发生了什么

把 Case5 的 StreamingFIR 与 Case04/T14 的 CoreML Session 接到同一条 BLE 叙事链：

`BLEPacket → RingBuffer → FIR 窗(25) → 8 维窗特征 → StandardScaler → Session.predict`

另加 `CoreMLStreamingInferenceActor` 演示串行推理边界。  
Golden：100 点合成 PPG → 4 窗 → 特征与概率冻结在 `golden/coreml_streaming/stream_report.json`。

**本 case 验证工程链路数值，不验证「活动分类是否临床正确」。**

## 2. 假设

- 无丢包时，流式窗输出 = 整段因果 FIR 再切窗。
- 特征公式与 scaler 固定后，Swift 概率可对齐 Python CoreML。
- Actor 不改变数值，只提供隔离。

## 3. 做法

- Python：`generate_coreml_streaming.py`
- Swift：`CoreMLStreamingPipeline` + `CoreMLStreamingInferenceActor`
- 测试：同步 parity + Actor parity

## 4. 数字

| 层 | 容差 |
| :--- | :--- |
| 窗特征 | abs ≤ 1e-9 |
| 概率 | abs ≤ 5e-4 |

环境：Mac Debug · Apple Silicon（与 T14 同栈）。

## 5. 坑与排查（摘要）

| 现象 | 优先查 |
| :--- | :--- |
| 特征偏 | std 是否 ddof=0；FIR 是否误 reset；packets/系数 |
| 特征对、概率偏 | scaler 是否 Case04；是否喂错模型包 |
| 仅 Actor 挂 | 重复 ingest 同一 pipeline；漏 `await` |
| 窗数不对 | `n_samples` 能否整除 25；丢包策略 |

完整分层排查见对齐口径 §4。

## 6. 结论

**流式 FIR 与缓存 CoreML Session 可以接到同一条 BLE 链；对不齐时先特征后概率。**

## 7. 面试卡片

- 分片 → 环缓 → FIR 窗 → 特征 → 缓存推理。
- compile 在 load；Actor 管并发。
- 黄金集钉死窗特征公式，防止随口改特征导致静默漂移。
