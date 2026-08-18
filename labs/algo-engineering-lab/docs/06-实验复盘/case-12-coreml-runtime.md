# Case12 实验复盘：CoreML 运行时工程化

版本：0.1.0 · 日期：2026-07-29 · 作者：lab · 状态：草稿

> 零基础：[`docs/09-CoreML入门/03-CoreML运行时与硬件.md`](../09-CoreML入门/03-CoreML运行时与硬件.md)  
> 对齐口径：[`docs/02-算法对齐口径/coreml-runtime-engineering.md`](../02-算法对齐口径/coreml-runtime-engineering.md)

---

## 1. 假设

- T13 里 CoreML「推理」p50 ≈ 42 ms，主要是每次 `compileModel`，不是小 MLP 前向本身。
- 缓存 `Session` 后，纯推理应比 compile 路径低至少一个数量级（本机实测约三个数量级）。
- 小 tabular MLP 在 Mac Debug 上 `.cpuOnly` 与 `.all` 可能接近；仍要分行列出，避免口嗨。

## 2. 做法

- `CoreMLActivityModel.load`：compile 一次 + `MLModelConfiguration.computeUnits`。
- `Session.predict`：只做 `MLMultiArray` + `prediction`。
- Parity：同一 Session 对 `verification_vectors` 多向量对齐（容差同 Case04）。
- Bench：`compile_every_call` / `infer_cached_all` / `infer_cached_cpu`。

## 3. 数字

| 实现 | p50 (ms) | p95 (ms) | 备注 |
| :--- | ---: | ---: | :--- |
| compile_every_call | 42.0520 | 43.9750 | 旧路径；含 compile |
| infer_cached `.all` | 0.0380 | 0.0479 | T14 纯推理 |
| infer_cached `.cpuOnly` | 0.0380 | 0.0559 | 本机与 `.all` 接近 |

相对 compile 路径，缓存纯推理 p50 加速约 **1100×**（42.05 / 0.038）——说明的是计量口径，不是「模型变快了 1100 倍」。

环境：Mac / Apple M2 / macOS 26.3.1 / Xcode 26.6 / **Debug** / 电源·常温。完整表见 [`docs/bench-log.md`](../bench-log.md)。

重跑：

```bash
swift test --filter UnifiedPerfPowerBenchmarkTests
swift test --filter CoreMLModelUsageParityTests
```

## 4. 坑

- 把含 compile 的数字讲成「端侧推理延迟」会直接误导面试与优化优先级。
- `predictProbabilities` 仍每次 load，仅留作对照；产品路径必须用 `Session`。
- Debug + 合成小模型数字不能直接当真机 ANE 结论。

## 5. 结论

**先缓存再测纯推理；compile 与 infer 分列 bench-log。**

## 6. 面试卡片（≤5）

- compile 一次、infer 多次；热路径禁止反复 `compileModel`。
- 我报的是拆开后的 p50/p95，并标明 computeUnits。
- 旧 42ms 是编译主导；缓存后本机约 0.04ms 量级（Debug·小 MLP）。
- 预处理仍单源：Session 吃的是 scaled 特征。
- 本仓库验证性原型，非生产睡眠/运动模型。
