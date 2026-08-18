---
title: "T8 教练出题集：VisionKit 与系统视觉能力"
topics: [learning, coreml, visionkit, vision, system-frameworks]
type: note
date: 2026-08-17
---

# T8 教练出题集：VisionKit 与系统视觉能力（独立增量轮）

> 本轮补「系统视觉能力」：VisionKit（ImageAnalyzer / Live Text / DataScanner / VNDocumentCamera）与 Vision 的关系，以及「系统能力优先、自定义 CoreML 兜底」的选型心智。
> 环境：Vision（VNRecognizeTextRequest）可在 macOS CLI 实跑；ImageAnalyzer/DataScanner 需要 App + 真机，按纪律标「待真机验证」。
> 使用纪律：卡住按弱→中→强逐级要提示（密卷在教练分支），直接要答案 → 反问「这是系统能力还是自定义模型」。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | 存量锚点 |
|---|------|-----------|---------|
| M1 | VisionKit 是系统视觉能力的 Swift 壳 | ImageAnalyzer（Live Text/视觉查找/翻译/二维码）、DataScannerViewController（实时扫描）、VNDocumentCameraViewController（文档扫描） | 已有：Vision 请求编排 |
| M2 | 系统能力优先 | 苹果内建 = on-device、免费、隐私好、维护零；自定义 CoreML 只在能力不足时 | 已有：T3 内建 vs 自定义 |
| M3 | Live Text 是「文本即交互」 | ImageAnalysisInteraction 把识别结果变成可点/可复制/可翻译的交互层 | 已有：OCR 管线心智 |
| M4 | 实时扫描是相机管线 | DataScannerViewController 管相机+识别+UI；回调与线程要按系统约定 | 已有：相机/权限心智 |
| M5 | 隐私与权限是卖点也是约束 | on-device 处理、相机授权、数据不出设备；威胁模型沿用 T5 C6 | 已有：隐私威胁模型 |

学员自检：合上表复述 M1–M5，各举一个「先用系统能力、不够再自定义」的例子。

## 二、争议：3 个焦点

**D1 VisionKit 会不会让自定义 OCR 模型失业？**
- 正：Live Text 质量高、免费、on-device；自定义投入大。
- 反：语言覆盖、领域词、定制输出格式、离线旧系统仍需要自定义。
- 迁移者意义：先跑内建，质量/覆盖/定制不达标再自定义，记账决定。

**D2 DataScanner 自建相机 + Vision 怎么选？**
- 正：DataScanner 开箱即用，UI/相机/识别全管。
- 反：要自定义相机体验（滤镜/取景框/多区域）时自建可控。
- 迁移者意义：默认 DataScanner；自定义相机体验需求是升级信号。

**D3 系统能力的上限在哪？**
- 正：语言、识别质量、输出结构化程度。
- 反：系统版本门槛（iOS 16+）、定制性。
- 迁移者意义：上限 = 语言覆盖 + 结构化输出 + 系统版本；超限再自定义。

## 三、概念拷问题（6 道）

### C1 VisionKit / Vision / CoreML 的关系？

画出三层：VisionKit（产品能力壳）、Vision（请求编排 + 内建模型）、CoreML（执行引擎）；说明各自管什么、谁依赖谁。

### C2 ImageAnalyzer 与 Live Text 的关系？

说明 `ImageAnalyzer` 的请求类型（`[.text, .visualLookup, .subject]`）、`ImageAnalysis` 结果、`ImageAnalysisInteraction` 如何把「识别」变成「可交互」（复制/翻译/查询/扫码）。

### C3 DataScannerViewController vs 自建相机 + Vision？

给出选择标准（开箱即用 vs 自定义体验），并说明 DataScanner 的能力（recognizedText/recognizedObjects/识别区域）与限制。

### C4 系统能力优先的选型流程？

写出判断链：需求 → 内建（Live Text/DataScanner/分类/文本）→ 不达标信号（语言/质量/定制）→ 自定义 Vision/CoreML → 记账。

### C5 VisionKit 的隐私与权限？

说明相机权限（NSCameraUsageDescription）、on-device 处理、数据不出设备的声明义务，以及与自定义模型的数据流差异。

### C6 升级到自定义 CoreML 的信号与成本？

列出至少三个「内建不够」的信号，以及升级路径（自定义 OCR 模型要重新面对 T2 资产流水线 + T7 造模）。

## 四、代码任务题（4 道，挂 Phase 8 载体）

落 `代码/T8/`；Q1 用 `swift` 实跑，Q2–Q4 可编译骨架 + 标注待真机/App 环境。

### Q1 Vision OCR 可跑代理

用 `VNRecognizeTextRequest` 对一张程序化生成的图片跑 OCR，打印识别文本与置信度——这是 Live Text 底层能力的 CLI 可跑代理。

### Q2 VisionKit API 骨架

写 `ImageAnalyzer` + `VKImageAnalysisRequest` + `ImageAnalysisInteraction` 的集成骨架（SwiftUI/UIKit 任选），标注哪些步骤需要 App 环境/真机验证；打印请求类型清单。

### Q3 三选一决策 CLI

输入场景描述，输出：系统能力（Live Text/DataScanner/内建分类）→ 自建 Vision 管线 → 自定义 CoreML 的决策与理由（记账）。

### Q4 权限与隐私检查清单

打印：相机权限文案、on-device 声明、数据不出设备、分析结果生命周期、与自定义模型数据流的差异说明。

## 五、验收规则

- 概念 6 题全过 + Q1 实跑 + Q2–Q4 骨架完整且待真机标注诚实；任一通道未过 → 不记过关。
- 系统能力优先的判断必须有信号与记账；「用内建就对了」= 半过。
- 本文件是题干版：提示与评分要点在 `T8-01-教练密卷-VisionKit与系统视觉能力.md`（仅教练分支，学员禁阅）。
