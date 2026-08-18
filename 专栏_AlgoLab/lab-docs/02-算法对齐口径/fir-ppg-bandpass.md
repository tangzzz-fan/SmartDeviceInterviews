# 对齐口径：PPG FIR 带通滤波（0.5–4 Hz）

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：生效

> Case2。系数一经冻结写入 `golden/fir_ppg/coeffs.json` 与 `Sources/AlgoC/include/algo_fir_coeffs.h`，禁止手改一侧。

---

## 1. 环节分解表

| 环节 | 参数 | 取值 | Python | iOS / C |
| :--- | :--- | :--- | :--- | :--- |
| 采样率 | fs | **25 Hz** | 常量 | 常量（文档约定，API 不传 fs） |
| 通带 | f_lo, f_hi | **0.5 Hz – 4.0 Hz**（心率基频附近） | `scipy.signal.firwin` | 使用导出系数 |
| 窗 / 阶数 | numtaps | **51**（奇数，I 型线性相位） | firwin | 同左 |
| 窗型 | window | **hamming** | firwin(window="hamming") | 体现在系数里 |
| 卷积 | 模式 | **same**：输出长度 = **len(x)**；边界外视为 0 | `scipy.signal.convolve(..., mode="same")`（**不要**用 `np.convolve` same） | naive / `vDSP_dotprD` 同公式 |
| 系数精度 | 导出 | **完整 double（printf %.17g）** | 生成脚本写出 | 头文件字面量 |
| 伪截断对照 | 演示 | 仅 6 位有效数字会破坏阻带 | 复盘记录 | 不进默认 parity |
| 病态 | 空 / NaN/Inf | 拒绝 | 同 HRV | `ALGO_ERR_EMPTY` / `NON_FINITE` |

---

## 2. 中间快照

| 快照名 | 格式 | 说明 | 比对阈值 |
| :--- | :--- | :--- | :--- |
| coeffs | number[] | 与实现共用的 b[k] | 逐元素 abs ≤ 1e-15（同文件） |
| y | number[] | 滤波输出 | 逐样本 abs ≤ 1e-4（相对 docs/01；本 case 信号约 ±1 量级） |

---

## 3. 已知差异 / 系数陷阱

| 差异点 | 量级 | 接受理由 | 确认人 |
| :--- | :--- | :--- | :--- |
| 系数只保留 6 位有效数字 | 阻带衰减可掉十余 dB，时域误差 ≫ 1e-4 | **禁止**作为默认导出；面试讲述陷阱用 | lab / scipy 实践 |
| naive C vs vDSP | 正常应在 1e-4 内 | 同一系数、同一 same 口径 | lab |
| Accelerate 内部舍入 | 极小 | 阈值按 docs/01 | lab |

---

## 4. 误差阈值（引用 docs/01）

滤波输出样本：**abs ≤ 1e-4**（输入为合成幅度约 1 的信号）。
