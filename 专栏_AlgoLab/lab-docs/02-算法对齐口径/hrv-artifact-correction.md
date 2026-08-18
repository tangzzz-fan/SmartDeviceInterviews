# 对齐口径：HRV 伪差校正（Artifact Correction）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

## 原理

HRV 对异常 RR（异位搏动、漏搏、连续噪声）高度敏感。  
校正链路通过「异常检测 → 插值回填」把输入拉回可计算区间，再进入时域/频域指标计算。

## 本 case 口径

- 异常判定：
  - RR 超出生理范围 `[300, 2000] ms` 直接标为伪差
  - 否则与局部邻域中位数（`i±1, i±2`，不含自身）比较，偏差大于 `120 ms` 标为伪差
- 回填策略：
  - 左右都有有效点：线性插值
  - 仅单侧有效：复制单侧值
  - 两侧都无有效：保留原值（理论上极少）
- 输出：`rr_raw`、`artifact_mask`、`rr_corrected`、校正后时域指标

## 中间快照

- `rr_raw`
- `artifact_mask`
- `rr_corrected`

## 验收阈值

- `rr_corrected` 与 Python 真值：abs ≤ `1e-9`
- `artifact_mask` 与 Python 真值：逐点一致
- 校正后 `SDNN/RMSSD`：abs ≤ `0.1ms`
- 校正后 `pNN50`：abs ≤ `0.5`
