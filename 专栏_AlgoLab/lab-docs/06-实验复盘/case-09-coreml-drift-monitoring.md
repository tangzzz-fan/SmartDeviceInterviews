# Case09 实验复盘：CoreML 在线漂移监控

版本：0.2.0 · 日期：2026-07-29 · 作者：lab · 状态：生效

> 对齐口径（含排查手册）：[`coreml-drift-monitoring.md`](../02-算法对齐口径/coreml-drift-monitoring.md)  
> 入门：[`../09-CoreML入门/04-预处理单源与量化语义.md`](../09-CoreML入门/04-预处理单源与量化语义.md) §3

---

## 1. 发生了什么

模型上线后，即使文件没换，输入分布变了（用户群体、固件版本、佩戴方式）也会让准确率 silently 掉。
T11 用 PSI（特征分布距离）和 KL（置信度分布距离）构建了一套 **可量化、可告警** 的漂移检测原型。

核心验收：稳定场景不过度告警；合成漂移场景稳定触发告警。

## 2. 假设

- 模型上线后输入分布偏移可先于精度下降出现，应被提前告警。
- 仅看均值方差不够，需加分布距离指标（PSI/KL）。
- 监控口径必须绑定训练期预处理参数，否则漂移告警会失真。

## 3. 做法

- 复用 T5 CoreML FP32 模型；若模型缺失，由 Python 自动重生。
- 构造 baseline / stable / shifted 三组样本（各 600 条），统一用 T5 的 scaler 参数归一化。
- 计算逐特征 PSI + 置信度分布 KL，并映射告警等级。

## 4. 数字

| 场景 | max_psi | kl_confidence | 告警级别 | 预期 |
| :--- | ---: | ---: | :--- | :--- |
| stable（同分布） | 小 | 小 | `low` | ✅ 不告警 |
| shifted（注入偏移） | 大 | 大 | `medium` 或 `high` | ✅ 告警 |

各特征 PSI 明细见 `golden/coreml_drift_monitoring/report.json` → `stable.feature_psi` / `shifted.feature_psi`。

断言：
- `stable_low_alert`：稳定场景 → `low` ✅
- `shifted_not_low`：漂移场景 → 非 `low` ✅
- `shifted_more_than_stable`：漂移指标 > 稳定指标 ✅

重跑：

```bash
uv sync --extra ml
uv run python -m python.generate_golden coreml_drift_monitoring
swift test --filter CoreMLDriftMonitoringParityTests
```

## 5. 坑

| 坑 | 影响 | 教训 |
| :--- | :--- | :--- |
| 监控口径必须绑定训练期预处理参数 | 否则漂移告警失真——监控的是自己的 bug | scaler 必须同源 |
| 只做单指标容易误报 | PSI 对某些分布不敏感 | PSI 与 KL 组合更稳健 |
| PSI 对 bin 数敏感 | bins 太少会丢信息，太多会过拟合 | 默认 10，可调参 |
| epsilon 不能太大 | 太大会平滑掉真实差异 | 用 `1e-8` |

## 6. 结论

**漂移监控是模型上线后的「早期预警层」，应与离线精度验证并行存在。**
监控链路本身也需要单源预处理——否则你在监控「自己预处理不一致的 bug」。

## 7. 面试卡片（≤5）

- 我把 CoreML 监控做成可重生脚本，不依赖手工导出。
- 上线后先看漂移，再看精度回归，避免事故后被动排查。
- 监控阈值用分层告警（low/medium/high），不是二元开关。
- PSI 盯特征分布、KL 盯置信度分布——组合比单指标稳健。
- 监控也要用训练期 scaler，否则漂移指标测的是你自己的 bug。
