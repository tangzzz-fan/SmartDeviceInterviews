---
title: "T7 教练出题集：Python 模型创建与转换"
topics: [learning, coreml, python, coremltools, conversion]
type: note
date: 2026-08-17
---

# T7 教练出题集：Python 模型创建与转换（独立增量轮）

> 本轮补「造模端」：用 Python（PyTorch + coremltools）创建并转换 CoreML 模型，把「只会接别人丢来的 .mlmodel」升级为「自己能用 Python 产出一个可部署的端侧模型」。
> 环境：`.venv`（Python 3.12，已装 numpy/torch/coremltools/httpx）；代码一律 `.venv/bin/python` 实跑。
> 使用纪律：卡住按弱→中→强逐级要提示（密卷在教练分支），直接要答案 → 反问「转换的输入到底是什么、输出契约是什么」。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | 存量锚点 |
|---|------|-----------|---------|
| M1 | Python 是造模端，CoreML 是部署端 | 训练框架 → coremltools 转换 → `.mlmodel` → 端侧 `.mlmodelc`；两端靠「数据契约」连接 | 已有：Swift 侧加载/预测 |
| M2 | coremltools 是转换器不是训练器 | 从 `torch.jit.trace` / TF SavedModel 转，或直接构建 ML Program；转换可能改算子、改精度 | 已有：Create ML 训练器 |
| M3 | 规范：NeuralNetwork vs ML Program | 新规范 ML Program 算子新、性能好、支持更好；旧规范兼容老模型 | 版本/兼容性心智 |
| M4 | 量化是部署决策 | fp16 / int8 / palettization：体积与延迟换精度；必须端侧回归 | 已有：T2 量化账本 |
| M5 | 契约由 Python 端定义 | 输入输出特征名/类型/形状（含 flexible）、预处理（归一化/通道/方向）在转换时钉死 | 已有：T1 数据契约 |

学员自检：合上表复述 M1–M5，各举一个自己会踩的坑。

## 二、争议：3 个焦点

**D1 直接转换 vs 为端侧重新训练？**
- 正：转换快、复用研究模型。
- 反：转换后算子/精度不可控；端侧友好训练（量化感知/小输入）更稳。
- 迁移者意义：先转换拿到基线，再评估是否需要端侧友好重训。

**D2 量化档位谁拍板？**
- 正：算法拍精度、客户端拍体积延迟——各有一票。
- 反：单一 owner 快，但容易偏科。
- 迁移者意义：量化账本（体积/延迟/指标）是共同决策依据。

**D3 生成的 .mlmodel 该不该进 git？**
- 正：可复现、团队共享。
- 反：二进制体积大、diff 无意义；脚本 + 版本号更优。
- 迁移者意义：优先「可复现脚本 + 产物哈希」，小模型可整包入库。

## 三、概念拷问题（6 道）

### C1 coremltools 转换的输入是什么？为什么是 trace 而不是整个模型？

说出 PyTorch 转 CoreML 的标准输入（`torch.jit.trace` 后的 ScriptModule 或 TorchScript），以及为什么转换需要「输入样例」（trace 是记录数据流不是读源码）；TF 侧对应什么（SavedModel）。

### C2 NeuralNetwork 与 ML Program 规范差在哪？

给出选择标准：算子支持、性能、可更新性、工具链新旧；新项目默认哪个。

### C3 转换后为什么要端侧回归？

说明转换可能改变什么（算子替换、精度、数值顺序），以及「Python 里 99% 不能直接引用」与 T2 C3 的关系。

### C4 量化的完整流程与验收？

写出 fp16 / int8（含 palettization 的概念）的流程：转换 → 量化 → 端侧回归 → 三指标验收（体积/延迟/任务指标）。

### C5 Python 端如何定义输入输出契约并与 Swift 对齐？

列出契约要素（特征名、类型、形状、预处理、标签表）以及 Python 转换脚本里如何声明（`ct.convert` 的 inputs/outputs 或模型元数据），Swift 端如何校验。

### C6 模型版本管理：二进制 vs 可复现脚本？

给出推荐：脚本 + 版本号 + 产物哈希；标签表/预处理版本与模型版本如何保持同步（回顾 T2 C5）。

## 四、代码任务题（4 道，挂 Phase 7 载体）

落 `代码/T7/`，`.venv/bin/python` 实跑，输出贴回。

### Q1 torch 微型分类器 → CoreML

用 torch 训练一个微型 MLP（如 4 输入 → 3 类，合成数据），`torch.jit.trace` → `coremltools.convert` → 保存 `model.mlpackage`（mlprogram 规范；classic 为 `.mlmodel`）；打印模型规格（输入/输出名、类型、形状）。

### Q2 转换前后对拍

同一输入样本，比较 torch 输出与 CoreML 输出（`ct.models.MLModel` 预测），打印最大绝对误差与 Top1 一致性。

### Q3 量化对比

对 Q1 模型做 fp16（及可选 int8/palettization）转换，打印：体积（fp32/fp16/量化后）、Top1 一致性、是否值得的结论（账本）。

### Q4 契约清单

打印：输入/输出特征名与类型与形状、预处理要求（归一化/通道顺序/方向）、标签表、版本三元组（模型语义版本/预处理版本/App 最低版本）。

## 五、验收规则

- 概念 6 题全过 + 代码 4 题全跑通；任一通道未过 → 不记过关。
- 对拍必须有数字（误差/一致性）；「看起来一样」不算。
- 本文件是题干版：提示与评分要点在 `T7-01-教练密卷-Python模型创建与转换.md`（仅教练分支，学员禁阅）。
