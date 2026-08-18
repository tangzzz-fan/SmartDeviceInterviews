# Case01 实验复盘：HRV 时域 parity

版本：0.1.0 · 日期：2026-07-28 · 作者：lab · 状态：草稿

---

## 1. 假设

- float64 路径下 C 与 Python 应对齐到远小于 0.1ms。
- 空/单点/NaN 错误码跨语言一致是比「算对正常样本」更容易翻车的地方。

## 2. 做法

- 先冻结对齐口径（不做伪差校正）。
- Python 固定 seed=42 生成 ≥50 条 golden，病态占比 ≥40%。
- C 用 double 累加；Swift 零拷贝 `withUnsafeBufferPointer` 调用。

## 3. 数字

| 指标 | 阈值 | 实测 | 环境 |
| :--- | :--- | :--- | :--- |
| SDNN/RMSSD | ≤0.1 ms | parity 全绿（见 CI 本地 `swift test`） | macOS + `swift test` Debug（精度断言；非性能） |
| pNN50 | ≤0.5 pp | 同上 | 同上 |
| 病态占比 | ≥40% | 生成脚本打印值 | uv + numpy/scipy |

> 性能数字留给 Benchmark；本复盘不把 Debug 单次耗时当面试数字。

## 4. 坑

- 测试进程 cwd 在 `.build` 下，golden 路径不能写死相对 cwd，需从 `#filePath` 向上找 repo 根。
- 空数组在 Swift 层提前抛 `.empty`，与 C 语义一致，但要保证 golden 的 `error` 字段也是 `empty`。

## 5. 结论

**数值一致性靠「口径文档 + 冻结 golden + 跨语言同一错误语义」，不是靠目测几个样例。**

## 6. 面试卡片（≤5）

- 我搭了 Python→golden→C/Swift 的 parity 流水线，错误码跨语言对齐。
- SDNN/RMSSD 中间用 double，阈值按产品无意义量级（0.1ms）而不是 1e-12。
- 本 case 故意关闭伪差校正，先锁公式再谈临床流水线。
- golden 只允许 Python 生成，禁止用 App 输出回写真值。
- 病态输入占比 ≥40%，专门覆盖 empty/single/NaN。
