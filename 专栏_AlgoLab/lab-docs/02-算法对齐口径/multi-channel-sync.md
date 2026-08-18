# 对齐口径：多通道同步与时间戳漂移校正

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

## 原理

多通道（如 PPG/ACC/EEG）分片传输会引入相位错位与时钟漂移。  
目标是重建统一时间轴，使跨通道分析在同一采样语义下进行。

## 本 case 口径

- 每包字段：`seq`、`channel_id`、`sample_count`、`t0`
- 对齐目标：统一到参考时基 `dt_ref`（单调递增）
- 映射规则：`idx = round(t / dt_ref)`，同 `seq` 排序后写入
- 漂移模型：线性漂移（ppm 级）优先，`t0` 已含漂移
- 缺口处理：`zero_fill`（本 case 固定），并同步输出 `mask`

## 中间快照

- `packets_raw`
- `timeline_rebuilt`
- `channels_aligned`

## 验收目标

- 注入漂移后可恢复对齐
- 丢包/乱序下仍可输出有定义的数据与 mask
- Swift 输出与 Python golden 的 `timeline/aligned/mask` 全量一致
