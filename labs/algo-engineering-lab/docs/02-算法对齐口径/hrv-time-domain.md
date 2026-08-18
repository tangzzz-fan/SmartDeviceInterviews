# 对齐口径：HRV 时域（SDNN / RMSSD / pNN50）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

> 模拟与算法工程师的对齐确认单。实现与 golden 必须服从本文档 + `docs/01`。

---

## 1. 环节分解表

| 环节 | 参数 | 取值 | Python | iOS / C |
| :--- | :--- | :--- | :--- | :--- |
| 输入 | 单位 | RR 间期，ms，float64 列表 | `list[float]` / numpy | `const double *rr_ms` |
| 最小长度 | N | ≥ 2 才可算 RMSSD/SDNN；pNN50 需 ≥2 | 同左 | `ALGO_ERR_TOO_SHORT` |
| 伪差校正 | 本 case | **不做**（先对齐原始公式；后续 case 可扩展） | identity | identity |
| SDNN | 定义 | 样本标准差：\(\sqrt{\frac{1}{N-1}\sum (RR_i-\bar{RR})^2}\)，N≥2 | `numpy.std(ddof=1)` | 中间累加 double |
| RMSSD | 定义 | \(\sqrt{\frac{1}{N-1}\sum (RR_{i+1}-RR_i)^2}\) | 手写与 numpy 等价 | 中间累加 double |
| pNN50 | 定义 | \(\|RR_{i+1}-RR_i\| > 50\) 的比例 ×100 | 手写 | 同左，输出百分点 |
| 非有限值 | NaN/Inf | 整段拒绝 | 检测后 raise/标记 | `ALGO_ERR_NON_FINITE` |
| 空输入 | — | 拒绝 | — | `ALGO_ERR_EMPTY` |

---

## 2. 中间快照

本 case 链路短，`snapshots` 可为 `{}`。可选快照：`mean_rr_ms`（便于对账）。

| 快照名 | 格式 | 路径字段 | 比对阈值 |
| :--- | :--- | :--- | :--- |
| mean_rr_ms | number | `snapshots.mean_rr_ms` | abs ≤ 1e-9（同 double 路径） |

---

## 3. 已知差异

| 差异点 | 量级 | 接受理由 | 确认人 |
| :--- | :--- | :--- | :--- |
| 未做 NeuroKit2 默认异位搏动处理 | 相对「临床流水线」可偏大 | 本 case 明确关闭伪差校正，先锁公式 | 参考本对齐口径 §1 |
| float32 累加版（若启用）相对 golden | 可 >0.1ms | 默认实现用 double；float32 仅作 drift 演示，不进默认 parity | lab |

---

## 4. 误差阈值（引用 docs/01）

SDNN/RMSSD abs ≤ 0.1 ms；pNN50 abs ≤ 0.5 百分点。
