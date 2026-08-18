# bench-log（追加式，禁止覆盖历史）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

> 格式见 `docs/05-性能基准规范.md`。五项环境缺一，数字无效。

| 日期 | commit | case | 实现 | p50 (ms) | p95 (ms) | 加速比 | 环境摘要 |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| 2026-07-28 | a7e8eb2 | fir_ppg N=200 | AlgoC naive | 0.034 | 0.039 | 1.0×（基准） | MacBook / Apple M2 / macOS 26.3.1 / Xcode 26.6 / **Debug** / 电源·常温 |
| 2026-07-28 | a7e8eb2 | fir_ppg N=200 | Swift vDSP_dotpr | 1.448 | 1.642 | 0.02× vs naive | 同上；Swift 逐点组窗开销主导 → 热路径应留在 C |
| 2026-07-28 | 2d80668 | unified_bench | FIR AlgoC naive | 0.0340 | 0.0380 | 1.0×（基准） | Mac / Apple M2 / macOS 26.3.1 / Xcode 26.6 / Debug / 电源·常温 |
| 2026-07-28 | 2d80668 | unified_bench | FIR Swift vDSP_dotpr | 1.4430 | 1.5470 | 0.0235× vs naive | 同上；逐点组窗开销依旧主导 |
| 2026-07-28 | 2d80668 | unified_bench | CoreML FP32 infer(8f) | 42.5091 | 46.9099 | — | 同上；含 `MLModel.compileModel` 路径开销 |
| 2026-07-28 | 2d80668 | unified_bench | Sleep postprocess(120 ep) | 0.1850 | 0.2040 | — | 同上；规则链路 CPU 开销低 |
| 2026-07-29 | b9285b8 | coreml_runtime T14 | compile_every_call | 42.0520 | 43.9750 | 1.0×（对照） | Mac / Apple M2 / macOS 26.3.1 / Xcode 26.6 / Debug / 电源·常温 |
| 2026-07-29 | b9285b8 | coreml_runtime T14 | infer_cached `.all` | 0.0380 | 0.0479 | ~1107× vs compile | 同上；Session 缓存后纯推理 |
| 2026-07-29 | b9285b8 | coreml_runtime T14 | infer_cached `.cpuOnly` | 0.0380 | 0.0559 | ~1107× vs compile | 同上；本机与 `.all` 接近 |

### 环境明细

| 字段 | 值 |
| :--- | :--- |
| 机型 | Mac（Apple M2） |
| 芯片 | Apple M2 |
| OS | macOS 26.3.1 (25D2128) |
| 编译配置 | `swift test` **Debug**（正式对比应改 Release） |
| 电量与发热 | 电源适配器；常温 |
| Xcode | Xcode 26.6 |

### 能耗补充（T13 记录模板）

| 字段 | 值 |
| :--- | :--- |
| 电源模式 | 接电 |
| 电量区间 | 80%-100%（人工观测） |
| 热状态 | 常温（无明显降频） |
| 监控工具 | Activity Monitor（轻量） |
| 备注 | 仅用于验证性原型；正式对外数字建议 Release + Instruments |
