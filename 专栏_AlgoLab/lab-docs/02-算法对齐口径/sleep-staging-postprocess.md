# 对齐口径：睡眠分期后处理（Post-processing）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

## 原理

逐 epoch 分类输出噪声高，直接展示会产生不合理跳转。  
后处理通过转移约束与时长约束，得到更平滑且可解释的 hypnogram。

## 本 case 口径

- 输入：每 30s 的 stage 概率
- 方法：规则后处理两步
  - 3 点多数平滑（majority3）
  - 单点跳变折叠（前后相同则吸附）
- 输出：平滑 stage 序列 + 统计指标（TST、SOL 等）

## 中间快照

- `stage_prob_raw`
- `transition_cost`
- `stage_smoothed`

## 验收目标

- 抖动频率明显下降
- 核心统计指标波动收敛
- Swift 与 Python 在 `raw/smoothed/metrics` 逐字段一致
