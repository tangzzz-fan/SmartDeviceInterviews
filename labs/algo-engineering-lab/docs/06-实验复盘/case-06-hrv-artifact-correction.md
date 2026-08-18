# Case06 实验复盘：HRV 伪差校正

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

## 1. 假设
- HRV 指标在存在异位/漏搏时会被离群点主导。
- 在固定口径下，先校正再算指标会比“直接计算”稳定。

## 2. 做法
- 先冻结口径：生理范围门控 + 局部中位数偏差阈值（120ms）+ 线性插值回填。
- Python 生成 golden（含 `rr_raw`、`artifact_mask`、`rr_corrected` 快照）。
- C 侧实现同口径；Swift 通过零拷贝调用 C，随后复用 Case1 时域指标计算。

## 3. 数字
- 见 `golden/hrv_artifact_correction` 与 `HRVArtifactCorrectionParityTests`。
- 关键阈值：`rr_corrected` abs≤1e-9、`SDNN/RMSSD` ≤0.1ms、`pNN50` ≤0.5。

## 4. 坑
- 连续异常段回填若只做“前向填充”会产生阶跃，需双侧插值优先。
- 非有限值（NaN/Inf）不能进 JSON，需用占位 + `non_finite_mode` 在测试侧复现。

## 5. 结论
- 伪差校正必须作为可验证的独立环节（有快照），不能只看最终 HRV 数字。

## 6. 面试卡片（≤5）
- HRV 的稳定性首先是输入质量问题，不是指标公式问题。
- 我把伪差校正拆成“检测+回填”并单独做 golden 快照对齐。
- 校正链路同样走 Python→C/Swift parity，避免“修了但不可证”。
