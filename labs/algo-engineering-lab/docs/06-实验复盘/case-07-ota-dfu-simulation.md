# Case07 实验复盘：OTA/DFU 状态机仿真

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

## 1. 假设
- OTA 成败关键在状态恢复，不在单次吞吐。
- 若中断路径未建模，系统会进入不可恢复未知态。

## 2. 做法
- 先冻结状态机：`idle -> prepare -> transferring -> verifying -> activating -> success`。
- 注入 `disconnect/app_restart/crc_error/fatal_error` 并定义恢复边。
- Python 生成 golden；Swift 状态机回放逐字段比对（终态 + 漏斗 + 进度）。

## 3. 数字
- 数据集：30 条事件序列，覆盖正常、可恢复失败与致命失败。
- 断言维度：`final_state`、`progress_chunks`、`funnel(started/transfer_completed/verified/activated)`。

## 4. 坑
- `target_chunks` 不一致会导致“看似通过但漏斗错位”，必须入参显式化。
- `resume_with_token` 只应从 `failed_recoverable` 生效，避免非法跳转。

## 5. 结论
- OTA 稳定性的核心交付物是可验证状态机，不是“传输成功一次”。

## 6. 面试卡片（≤5）
- 我把 OTA 先建成状态机再写代码，所有失败路径可回放。
- 断连/重启/CRC 错误都能落在可恢复或致命终态，不留未知态。
- 我用漏斗指标监控升级质量：开始、传输完成、校验、激活。
