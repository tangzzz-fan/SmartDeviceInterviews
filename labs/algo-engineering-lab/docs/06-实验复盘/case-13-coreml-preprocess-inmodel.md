# Case13 实验复盘：CoreML 预处理入模对照

版本：0.2.0 · 日期：2026-07-29 · 作者：lab · 状态：草稿

> 对齐口径（含排查手册）：[`coreml-preprocess-inmodel.md`](../02-算法对齐口径/coreml-preprocess-inmodel.md)  
> 入门：[`../09-CoreML入门/04-预处理单源与量化语义.md`](../09-CoreML入门/04-预处理单源与量化语义.md)

---

## 1. 发生了什么

把「预处理单源」从口号变成两条可运行路径 + 一条负例：

1. **路径 A**：App 做 StandardScaler，模型只吃 scaled（旧 Case04 包）。
2. **路径 B**：把同一套 mean/scale 烘进图（对角 linear），模型吃 raw。
3. **负例**：对 raw 做两次 scale 再喂 A，证明事故可被断言抓住。

同权下 A≈B（max abs ~7e-10）；负例整体 max abs ~0.99。  
注意：不是每条验证向量都大幅偏离——第 0 条可能只偏一点点，必须以 **全集最大偏离** 验收负例。

## 2. 假设

- 同 seed MLP + 同 scaler，图内实现应与 App 侧数值等价。
- 双重 normalize 会破坏输入分布，概率应显著偏离。

## 3. 做法

- 脚本：`python/generate_coreml_preprocess_inmodel.py`
- 测试：`CoreMLPreprocessInModelParityTests`
- 固定 3 条 raw，写入 `golden/coreml_preprocess_inmodel/compare_report.json`

## 4. 数字

| 指标 | 阈值 | 实测 |
| :--- | :--- | :--- |
| app vs in-model max abs | ≤1e-5 | ~7e-10 |
| double vs correct max abs | ≥0.01 | ~0.99 |

## 5. 坑与排查（摘要）

| 现象 | 优先查 |
| :--- | :--- |
| A/B 对不齐 | 喂错 raw/scaled；输入名写死；mean/scale 不一致 |
| 负例断言失败 | 误要求「每条都 ≥0.01」；应看全集 max |
| Case04 突然挂 | T15 覆写了 `activity_fp32` → 同步重生 `coreml_quant` |

完整表见对齐口径 §4。

## 6. 结论

**单源两种落地可对齐；双重 normalize 必须能被测试抓住。**

## 7. 面试卡片

- 预处理要么全在 App，要么全进模型。
- 我用同权双包 + 固定向量证明对齐。
- 负例按全集最大偏离验收，避免被「碰巧不敏感」的样本骗过。
