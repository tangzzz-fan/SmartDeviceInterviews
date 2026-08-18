# 对齐口径：OTA/DFU 断点续传状态机仿真

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

## 原理

OTA 的核心是状态机可恢复性：任何中断（断连/重启/CRC 错误）都必须可续传或可回滚到安全态。

## 状态

- `idle`
- `prepare`
- `transferring`
- `verifying`
- `activating`
- `success`
- `failed_recoverable`
- `failed_fatal`

## 关键事件

- `chunk_sent`
- `ack_received`
- `disconnect`
- `app_restart`
- `crc_error`
- `resume_with_token`

## 漏斗指标

- started
- transfer_completed
- verified
- activated

## 验收目标

- 中断场景均有确定迁移路径
- 同一输入事件序列得到稳定可复现终态
- Swift 回放与 Python golden 逐字段一致
