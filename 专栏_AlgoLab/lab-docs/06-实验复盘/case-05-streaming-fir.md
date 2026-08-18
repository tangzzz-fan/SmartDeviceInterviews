# Case05 实验复盘：流式 FIR + RingBuffer + 丢包

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

---

## 1. 假设

- 按 1 秒窗切 FIR 若不保留延迟线，边界必有跳变。
- BLE 分片到达与 DSP 连续流假设之间，需要 RingBuffer + 缺口策略。

## 2. 做法

- 流式改用**因果** FIR（与 Case2 `same` 分家，写进对齐口径）。
- C：`AlgoFIRStreamState` 延迟线；Swift：`SampleRingBuffer` + `StreamingFIRPipeline`。
- 丢包默认 `zero_fill`，与「预插零再整段因果滤波」golden 对齐；另测每窗 reset 负例。

## 3. 数字

| 检查 | 阈值 | 实测 | 环境 |
| :--- | :--- | :--- | :--- |
| 连续流式 vs 整段因果 | abs ≤ 1e-12 | 全绿 | macOS + `swift test` Debug |
| 5% 丢包 zero_fill | abs ≤ 1e-12 | 全绿 | 同上 |
| 每窗 reset 负例 | max abs ≫ 1e-6 | 通过（确有边界伪影） | 同上 |

## 4. 坑

- Case2 `mode=same` 非因果居中，不能直接当流式真值；必须单独冻结因果口径。
- 丢包填零需要知道「每包样点数」；本 lab 固定 packet_size=2 以保证可复现。
- 开流前缀丢包（首包 seq>0）也要补零，否则时间轴整体错位。

## 5. 结论

**流式 DSP 的价值在状态管理：窗口边界的延迟线 = BLE 分片与连续算法之间的缝合层。**

## 6. 面试卡片（≤5）

- 滤波器状态必须跨窗口连续，否则波形每秒跳变。
- 这和 BLE 收包同构：数据分片到，算法假设流连续。
- 丢包策略要可测：zero_fill 能与预插零 golden 对齐。
- 流式用因果 FIR；离线 same 对齐是另一条口径，不要混。
- 我用「错误每窗 reset」作负例，证明边界伪影可复现。
