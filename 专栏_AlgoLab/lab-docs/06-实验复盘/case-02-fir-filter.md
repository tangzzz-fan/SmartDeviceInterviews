# Case02 实验复盘：FIR PPG 带通

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

---

## 1. 假设

- 系数完整 double 导出后，C naive 与 scipy same 应对齐到 1e-4。
- 「只保留 6/3 位有效数字」会破坏频响（truncation_demo）。
- Accelerate 整段 `vDSP_conv` 若填充约定不对，会整体错位——优先口径正确。

## 2. 做法

- `scipy.signal.firwin` 设计 51 抽头带通；生成脚本同步写 `coeffs.json` + `algo_fir_coeffs.h`（`%.17g`）。
- **禁止**用 `np.convolve(..., same)`：短输入时长度为 `max(M,N)`；改用 `scipy.signal.convolve(..., same)`。
- C：直接型卷积对齐 same；Swift：`vDSP_dotprD` 按相同公式加速内积（保证与 golden 一致）。

## 3. 数字

见 `docs/bench-log.md` 追加行。本机一次本地结果（Debug）：

| 实现 | p50 (ms) | p95 (ms) | 备注 |
| :--- | ---: | ---: | :--- |
| AlgoC naive | ~0.034 | ~0.039 | N=200 @25Hz×8s |
| Swift+vDSP_dotpr | ~1.45 | ~1.64 | 逐点组窗开销大 |

结论：热路径应留在 C/整段内核，而不是 Swift 层逐点拼窗。

## 4. 坑

1. `np.convolve` same ≠ `scipy.signal.convolve` same（短序列）。
2. C 定长数组进 Swift 变成 tuple，要用 `withUnsafePointer` 读。
3. `vDSP_convD` 缓冲/反转稍错就整段对不上——parity 比「感觉加速」优先。

## 5. 结论

**系数精度 + 卷积口径 + 跨语言同一 golden，是 FIR 工程化的三条腿；加速只能在口径锁定之后做。**

## 6. 面试卡片

- 我会把 firwin 系数以完整 double 导出到 C 头文件，并单独演示截断有效位的误差。
- golden 用 scipy `convolve(same)`，并写明不要用 numpy same。
- C naive 与 Accelerate 路径过同一套 golden；加速比带机型五项记录。
- Swift↔C 按帧批量，避免逐 sample 跨边界。
- 验证性原型口径，不伪装成量产 DSP 库。
