# Tickets: algo-engineering-lab

验证性原型：Python 算法原型 → golden → C/Swift → parity 回归。  
规格来源：`Talk with K3/algo-engineering-lab技术文档要求说明书.md`。

Work the **frontier**：blocker 全完成后即可开工。线性上优先 T0 → T1 → T2。

## T0 · 仓库骨架 + uv 环境 + 三份核心规范初稿

**What to build:** 可克隆的 lab 仓库；用 `uv` 一键同步 Python 环境；`docs/01`、`03`、`05` 初稿可指导后续 case；目录与 README 定位清晰。

**Blocked by:** None — can start immediately.

- [x] `algo-engineering-lab/` 目录结构符合说明书 1.1
- [x] `uv sync` 可进入虚拟环境（依赖锁定）
- [x] `docs/01-数值一致性规范.md`、`03-黄金数据集规范.md`、`05-性能基准规范.md` 含元信息与必填表格骨架
- [x] README 含一句话定位、链路图、快速开始（≤3 条命令进环境）

## T1 · C 库集成规范 + SPM/C 目标可编译空壳

**What to build:** Swift Package 能 `swift build`；Parity / Benchmark 测试目标分离；C 集成规范可对照 review。

**Blocked by:** T0 · 仓库骨架 + uv 环境 + 三份核心规范初稿

- [x] `docs/04-C库集成规范.md` 含职责/所有权/零拷贝/批次/错误码/线程
- [x] `Package.swift` 定义 AlgoC、AlgoSwift、ParityTests、BenchmarkTests
- [x] `swift build` 成功
- [x] `swift test --filter ParityTests` 冒烟通过

## T2 · Case1 HRV 时域：端到端 parity 全绿

**What to build:** 输入 RR 间期，输出 SDNN/RMSSD/pNN50；Python 生成 golden；C + Swift 实现过同一套 parity。

**Blocked by:** T0 · 仓库骨架 + uv 环境 + 三份核心规范初稿；T1 · C 库集成规范 + SPM/C 目标可编译空壳

- [x] 对齐口径文档 `docs/02-算法对齐口径/hrv-time-domain.md`
- [x] `uv run` 生成 golden，覆盖正常/边界/病态，病态占比 ≥40%
- [x] Parity 测试全绿；复盘草稿 `docs/06-实验复盘/case-01-hrv-time-domain.md`

## T3 · Case2 FIR 滤波：C 卷积 vs vDSP + 系数精度

**What to build:** PPG 带通滤波；scipy 系数导出；naive C 与 vDSP 同 golden；记录加速比。

**Blocked by:** T2 · Case1 HRV 时域：端到端 parity 全绿

- [x] 对齐口径含系数有效位陷阱
- [x] naive 与 vDSP 均过同一 golden
- [x] benchmark 记录含机型/芯片/iOS或macOS/配置/电量发热五项

## T4 · Case3 HRV 频域：中间快照逐环对齐

**What to build:** LF/HF 链路；每环中间快照；跨平台口径差异表。

**Blocked by:** T2 · Case1 HRV 时域：端到端 parity 全绿

- [x] `docs/02-算法对齐口径/hrv-freq-domain.md` 环节表完整
- [x] 逐快照比对通过

## T5 · Case4 CoreML 量化漂移（FP32 vs FP16）

**What to build:** 小模型 FP32/FP16 对比；top-1 一致率与置信度分布；预处理单源约定。

**Blocked by:** T0 · 仓库骨架 + uv 环境 + 三份核心规范初稿；T2 · Case1 HRV 时域：端到端 parity 全绿

- [x] 量化对比报告可复现
- [x] 文档口径为验证性原型，非生产项目

## T6 · Case5 流式滑窗：RingBuffer + FIR overlap + 丢包注入

**What to build:** 模拟 BLE 分片到达；滑窗 FIR 无边界跳变；缺口策略可演示。

**Blocked by:** T3 · Case2 FIR 滤波：C 卷积 vs vDSP + 系数精度

- [x] 窗口边界无跳变可验证
- [x] 注入丢包/乱序时行为符合对齐口径

## T7 · README 结果看板收口 + 三张面试口述卡片

**What to build:** 精度表 + 性能表收口；三张口述卡片（精度漂移 / C 集成 / 流式状态）。

**Blocked by:** T2 · Case1 HRV 时域：端到端 parity 全绿；T3 · Case2 FIR 滤波：C 卷积 vs vDSP + 系数精度；T4 · Case3 HRV 频域：中间快照逐环对齐；T5 · Case4 CoreML 量化漂移（FP32 vs FP16）；T6 · Case5 流式滑窗：RingBuffer + FIR overlap + 丢包注入

- [x] 陌生人按 README 15 分钟内跑通已完成 case 的 parity
- [x] 三张卡片各 ≤5 条 bullet，可被追问一层

---

## Phase 2 · 候选扩展 Case（T8+）

来源：`docs/08-扩展案例建议.md`。  
原则不变：Python 原型 → golden → C/Swift → parity/benchmark → 复盘。

## T8 · Case A：HRV 伪差校正（Artifact Correction）

**Principle（原理）：** RR 序列中异位搏动/漏搏会导致 HRV 指标偏移；通过异常点检测 + 插值回填提高指标鲁棒性。  
**What to build:** 在 Case1 前增加 correction 链路；对比校正前后指标与误差稳定性。  
**Blocked by:** T2 · Case1 HRV 时域：端到端 parity 全绿

- [x] 对齐口径文档：`docs/02-算法对齐口径/hrv-artifact-correction.md`
- [x] Python golden 覆盖 ectopic/missing/连续异常段，病态占比 ≥40%
- [x] C/Swift 与 Python correction 后结果 parity 全绿
- [x] 复盘文档：`docs/06-实验复盘/case-06-hrv-artifact-correction.md`

## T9 · Case C：OTA/DFU 断点续传状态机仿真（协议侧）

**Principle（原理）：** OTA 的核心是可恢复状态机，不是文件传输；必须保证中断后可续传或安全失败。  
**What to build:** 模拟 chunk/ack/resume token；注入断连、重启、CRC 错误，输出漏斗指标。  
**Blocked by:** T1 · C 库集成规范 + SPM/C 目标可编译空壳

- [x] 状态机文档：`docs/02-算法对齐口径/ota-dfu-state-machine.md`
- [x] 仿真脚本 + golden：中断场景可复现
- [x] Swift 侧状态机回放与 golden 对齐
- [x] 复盘文档：`docs/06-实验复盘/case-07-ota-dfu-simulation.md`

## T10 · Case B：多通道同步与时间戳漂移校正

**Principle（原理）：** 多通道信号在 BLE 分片下会产生时间错位；需统一时间轴与漂移校正。  
**What to build:** 通道序列号 + 时间戳重建；比较校正前后对齐误差。  
**Blocked by:** T6 · Case5 流式滑窗：RingBuffer + FIR overlap + 丢包注入

- [x] 对齐口径文档：`docs/02-算法对齐口径/multi-channel-sync.md`
- [x] Golden 含时钟漂移 + 丢包/乱序注入
- [x] Swift 重建输出与 Python 真值对齐
- [x] 复盘文档：`docs/06-实验复盘/case-08-multi-channel-sync.md`

## T11 · Case E：CoreML 在线漂移监控（Monitoring）

**Principle（原理）：** 线上输入分布变化会导致模型性能退化；需用统计指标持续监控。  
**What to build:** 输入分布统计 + PSI/KL 漂移指标 + 告警阈值策略。  
**Blocked by:** T5 · Case4 CoreML 量化漂移（FP32 vs FP16）

- [x] 对齐口径文档：`docs/02-算法对齐口径/coreml-drift-monitoring.md`
- [x] 报告脚本：正常/漂移场景阈值可区分
- [x] Parity 测试断言告警触发逻辑
- [x] 复盘文档：`docs/06-实验复盘/case-09-coreml-drift-monitoring.md`

## T12 · Case D：睡眠分期后处理（Post-processing）

**Principle（原理）：** 单 epoch 分类噪声大；利用 HMM/规则约束平滑转移，提升可解释性。  
**What to build:** 输入分类概率序列，输出平滑 hypnogram 与稳定统计指标。  
**Blocked by:** T5 · Case4 CoreML 量化漂移（FP32 vs FP16）

- [x] 对齐口径文档：`docs/02-算法对齐口径/sleep-staging-postprocess.md`
- [x] Golden 含抖动场景 + 约束后期望输出
- [x] Swift 后处理链路 parity 全绿
- [x] 复盘文档：`docs/06-实验复盘/case-10-sleep-staging-postprocess.md`

## T13 · Case F：端上性能与能耗画像（Perf + Power）

**Principle（原理）：** 算法可用不等于可上线；需量化延迟、吞吐、内存和功耗趋势。  
**What to build:** C naive / Accelerate / CoreML 多实现统一基准；退化门槛检测。  
**Blocked by:** T3 · Case2 FIR 滤波：C 卷积 vs vDSP + 系数精度；T5 · Case4 CoreML 量化漂移（FP32 vs FP16）

- [x] 基准规范补充：`docs/05-性能基准规范.md` 增加能耗记录模板
- [x] BenchmarkTests 增加统一对比入口
- [x] `docs/bench-log.md` 追加可复现数字（含环境五元信息）
- [x] 复盘文档：`docs/06-实验复盘/case-11-perf-and-power.md`

## T14 · Case12：CoreML 运行时工程化（缓存 compile + computeUnits）

**Principle（原理）：** compile 与 infer 必须拆开计量；热路径只做 prediction，并用 `MLComputeUnits` 对照。  
**What to build:** `Session` 缓存、`cpuOnly`/`all` bench、入门文档回链、case-12 复盘。  
**Blocked by:** T5 · Case4 CoreML 量化漂移（FP32 vs FP16）

- [x] 对齐口径：`docs/02-算法对齐口径/coreml-runtime-engineering.md`
- [x] `CoreMLActivityModel.load` + `Session.predict`；parity 用缓存 Session
- [x] Benchmark 输出 compile_every_call / infer_cached（cpu / all）；`bench-log` 追加
- [x] 复盘：`docs/06-实验复盘/case-12-coreml-runtime.md`
- [x] 入门体系：`docs/09-CoreML入门/`（00–04）

## T15 · 预处理入模对照

**Principle（原理）：** 预处理单源可用「烘进模型」或「全在 App」实现；双路径须数值对齐，并覆盖双重 normalize 负例。  
**What to build:** 同权两份 mlpackage（App-scaler vs in-model-scaler）+ 负例测试。  
**Blocked by:** T14 · Case12：CoreML 运行时工程化

- [x] 对齐口径与 golden 对照向量
- [x] Swift / Python 双路径 parity
- [x] 复盘 + 入门 `04` 增补对照实验小节

## T16 · 滑窗 Actor 接 StreamingFIR

**Principle（原理）：** BLE 分片 → 滤波 → 特征窗满 → CoreML 推理，与可穿戴主场叙事同构。  
**What to build:** Actor 串行推理 + 现有 RingBuffer/StreamingFIR 触发。  
**Blocked by:** T6 · Case5 流式滑窗；T14 · Case12：CoreML 运行时工程化

- [x] 对齐口径与端到端 golden
- [x] Swift 滑窗触发 + Session 复用
- [x] 复盘 + 入门 `03` 流式附录
