# 对齐口径：CoreML 运行时工程化（编译缓存与 computeUnits）

版本：0.1.0 · 日期：2026-07-29 · 作者：lab · 状态：生效

> Case12 / T14。零基础请先读 [`docs/09-CoreML入门/03-CoreML运行时与硬件.md`](../09-CoreML入门/03-CoreML运行时与硬件.md)。  
> 验证性原型：用现有 `activity_fp32.mlpackage` 证明「compile 与 infer 必须拆开计量」。

---

## 1. 环节分解表

| 环节 | 参数 | 取值 | Python | iOS / CoreML |
| :--- | :--- | :--- | :--- | :--- |
| 模型 | — | Case04 FP32 活动三分类 | `artifacts/coreml/activity_fp32.mlpackage` | 同包 |
| 编译 | — | `MLModel.compileModel(at:)` | — | **会话级一次**；禁止热路径每次调用 |
| 配置 | computeUnits | `.cpuOnly` / `.all`（本 lab 对照） | — | `MLModelConfiguration` |
| 推理 | input | 已 scaled 的 8 维 float | CoreML runtime | `Session.predict` → `MLMultiArray` |
| 基准 | — | 预热后 N≥30；分位数 p50/p95 | — | `UnifiedPerfPowerBenchmarkTests` |

---

## 2. API 契约

| API | 行为 | 用途 |
| :--- | :--- | :--- |
| `CoreMLActivityModel.load(modelURL:computeUnits:)` | compile + load → `Session` | 生产路径 |
| `Session.predict(features:)` | 仅 prediction | 热路径 |
| `predictProbabilities(...)` | 每次 load（含 compile） | 对照 bench / 偶发调用 |

输入仍须满足 Case04 预处理单源：喂 **scaled** 向量。

---

## 3. 指标与阈值（lab）

| 指标 | 定义 | 验收 |
| :--- | :--- | :--- |
| `compile_every_call` | 旧路径单次墙钟 | 记录对照；预期远大于纯推理 |
| `infer_after_cached_load` | Session 上反复 predict | 记录；应明显低于 compile 路径 |
| `infer_cpuOnly` vs `infer_all` | 同模型换 computeUnits | 记录差异；小模型可能接近 |
| Parity | `verification_vectors` | 缓存 Session 下容差与 Case04 相同 |

禁止把「含 compile 的 42ms」口述成「推理延迟」。

---

## 4. 产物路径

| 产物 | 路径 |
| :--- | :--- |
| 实现 | `Sources/AlgoSwift/CoreMLActivityModel.swift` |
| 基准 | `Tests/BenchmarkTests/UnifiedPerfPowerBenchmarkTests.swift` |
| 数字 | `docs/bench-log.md`（追加，不覆盖） |
| 复盘 | `docs/06-实验复盘/case-12-coreml-runtime.md` |

## 5. 排查手册（出问题怎么查）

### 5.1 Session 加载失败

| 检查项 | 怎么做 |
| :--- | :--- |
| `.mlpackage` 路径 | 确认路径可达；测试用 `locate` 方法是否指向 `artifacts/coreml/` |
| 目录结构完整 | 需含 `Manifest.json`、`Data/com.apple.CoreML/`、`weights/` |
| 已编译 vs 未编译 | 不能对 `.mlpackage` 直接 `MLModel(contentsOf:)`；必须先 `compileModel` |
| 磁盘空间 | `compileModel` 写临时目录；空间不足会失败 |

### 5.2 bench 数字异常

| 检查项 | 怎么做 |
| :--- | :--- |
| compile 混入了 infer | 确认 `compile_every_call` 和 `infer_cached` 分开测 |
| 预热不够 | 前 N 次是 warm-up，只取稳定后的 p50/p95 |
| Debug vs Release | Debug 含符号、优化低；正式对比要 Release |
| 首次 ANE 调度延迟 | 首次 `.all` 路径可能比后续慢（ANE 初始化） |

### 5.3 computeUnits 似乎不生效

| 检查项 | 怎么做 |
| :--- | :--- |
| 模型太小 | 本 lab 195 参数 MLP，ANE/GPU 启动开销 > 计算节省 → `.all` 与 `.cpuOnly` 接近 |
| 算子不支持 | 部分算子 ANE 不支持会 fallback CPU；用 Instruments 确认 |
| Mac vs iPhone | Mac 的 ANE 行为与 iPhone 不同；勿直接搬数字 |

---

## 6. 已知差异

| 差异点 | 量级 | 接受理由 | 确认人 |
| :--- | :--- | :--- | :--- |
| Mac Debug vs 真机 Release | 大 | 本 lab 先证明计量口径；对外数字须重测 | lab |
| 小 MLP 上 ANE 收益可能不明显 | 中 | 仍要有对照行，避免「默认 .all」口嗨 | lab |
| `compileModel` 每次写临时 `.mlmodelc` | 中 | 正是旧路径慢的主因之一 | lab |

---

## 6. 面试金句

> compile 和 infer 必须拆开计量；我先缓存 Session，再报纯推理 p50/p95，并用 cpuOnly / all 对照，而不是把 40ms 编译开销说成模型推理。
