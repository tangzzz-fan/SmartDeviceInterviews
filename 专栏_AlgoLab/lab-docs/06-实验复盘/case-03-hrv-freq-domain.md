# Case03 实验复盘：HRV 频域 + 中间快照

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

---

## 1. 假设

- 跨平台频域对不上，首因是前置链路口径，不是 FFT 库本身。
- 逐环快照（resampled → detrended → windowed → psd → LF/HF）能把漂移定位到「哪一环」。

## 2. 做法

- 冻结口径：`docs/02-算法对齐口径/hrv-freq-domain.md`（4Hz 线性插值、减均值、Hann、\(P=|X|^2/N^2\)、LF/HF 边界不双计）。
- Python 生成 53 条 golden（病态约 53%），每条带全链路快照。
- C 用朴素 rDFT（与 `numpy.fft.rfft` 同定义）；Swift 零拷贝取快照做 parity。

## 3. 数字

| 指标 | 阈值 | 实测 | 环境 |
| :--- | :--- | :--- | :--- |
| 时域快照 | abs ≤ 1e-9 | 全绿 | macOS + `swift test` Debug |
| PSD | abs≤1e-9 或 rel≤1e-12 | 全绿（ULP 级差） | 同上 |
| LF/HF | 相对 1% 或 abs 1e-6 | 全绿 | 同上 |
| 病态占比 | ≥40% | 52.83% | uv 生成脚本 |

## 4. 坑

- JSON 不能存 NaN：生成时必须用真实 NaN/Inf 调原型拿 `error`，序列化时再清零 + `non_finite_mode`。
- Swift 无法导入带括号的宏表达式 → `ALGO_HRV_FREQ_MAX_PSD` 写成字面量 `2049`。
- LF/HF 在 0.15Hz 必须单边归属，否则功率双计导致 ratio 系统性偏。

## 5. 结论

**频域对齐的交付物是「环节表 + 中间快照」，不是「又一个 LF/HF 数字」。**

## 6. 面试卡片（≤5）

- 频域对不上先查重采样/去趋势/窗/归一化，不要先怪 FFT。
- 我用中间快照逐环定位，和 BLE 分层抓包同构。
- numpy.fft 不做 1/N，功率定义必须写进对齐文档。
- LF/HF 边界约定要写死，避免 0.15Hz 双计。
- golden 只允许 Python 写，快照与标量同一套真值。
