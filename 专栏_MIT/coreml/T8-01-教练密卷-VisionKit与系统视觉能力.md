# T8-01 教练密卷：VisionKit 与系统视觉能力（仅教练分支/归档，学员禁阅）

> 本文件含弱/中/强三级提示、评分要点与参考答案。使用纪律：直接要答案 → 反问「这是系统能力还是自定义模型」。

## 一、概念题：提示梯与评分要点

### C1 三层关系
- 弱提示：VisionKit 管产品能力、Vision 管请求编排、CoreML 管执行——谁在上谁在下？
- 中提示：ImageAnalyzer 底层调的是谁？VNCoreMLRequest 是 CoreML 的什么？
- 强提示：VisionKit（产品壳）→ Vision（编排 + 内建）→ CoreML（执行引擎）；VNCoreMLRequest 把 CoreML 模型包成 Vision 请求。
- 评分要点：真懂特征：三层依赖关系；死记硬背典型：「都是苹果的框架差不多。」
- 参考答案：VisionKit 依赖 Vision，Vision 依赖 CoreML；各自管产品能力/编排/执行。

### C2 ImageAnalyzer 与 Live Text
- 弱提示：分析请求有哪些类型？结果对象是什么？交互层是谁？
- 中提示：ImageAnalysis 里文本/视觉查找/主体分别是什么？Interaction 把结果变成什么？
- 强提示：`ImageAnalyzer.analyze(_:configuration:completion:)` 产 `ImageAnalysis`；`ImageAnalysisInteraction` 提供复制/翻译/查询/扫码/主体抠图交互。
- 评分要点：真懂特征：请求类型 + 交互能力；死记硬背典型：「VisionKit 就是 OCR。」
- 参考答案：请求类型 .text/.visualLookup/.subject；结果 ImageAnalysis；交互靠 ImageAnalysisInteraction。

### C3 DataScanner vs 自建
- 弱提示：DataScanner 管了什么（相机/识别/UI）？自建要补什么？
- 中提示：自定义取景框/多区域/滤镜——哪些是 DataScanner 给不了的？
- 强提示：默认 DataScanner（开箱即用，recognizedText/recognizedObjects/识别区域）；自建（AVCaptureSession + Vision）只在自定义相机体验或特殊识别布局时。
- 评分要点：真懂特征：默认 + 升级信号；死记硬背典型：「自建更灵活。」
- 参考答案：默认 DataScanner；自建信号 = 自定义相机体验/特殊布局。

### C4 系统能力优先流程
- 弱提示：判断链第一问是什么（需求是否被内建覆盖）？
- 中提示：不达标信号（语言/质量/结构化输出）出现才往自定义走？
- 强提示：需求 → 内建覆盖？→ 不达标信号 → 自定义 → 记账（成本/收益/撤出）。
- 评分要点：真懂特征：完整判断链 + 信号；只有「用内建」= 半过。
- 参考答案：先内建，信号驱动升级，记账收尾。

### C5 隐私与权限
- 弱提示：相机要什么权限文案？分析在设备上还是云端？
- 中提示：on-device 是默认还是配置？数据生命周期怎么管？
- 强提示：NSCameraUsageDescription 必填；ImageAnalyzer/DataScanner 默认 on-device；数据不出设备要在隐私说明声明；结果对象生命周期要管理。
- 评分要点：真懂特征：权限 + on-device + 声明义务。
- 参考答案：权限文案 + on-device 默认 + 隐私声明 + 结果生命周期。

### C6 升级信号与成本
- 弱提示：语言覆盖不够、领域词识别差、要结构化输出——这些是信号吗？
- 中提示：自定义 OCR 意味着重新面对什么（资产流水线/造模/量化/回归）？
- 强提示：三个信号：语言覆盖、领域词质量、结构化输出；升级成本 = T2 流水线 + T7 造模 + 端侧回归全套。
- 评分要点：真懂特征：信号 + 成本链条；死记硬背典型：「内建不行就自己训。」
- 参考答案：信号驱动，成本 = 整条模型资产流水线。

## 二、争议焦点参考立场

- D1 OCR 失业论：内建覆盖 80% 场景；定制/语言/覆盖不达标再自定义，记账决定。
- D2 DataScanner vs 自建：默认 DataScanner；自定义相机体验是唯一强升级信号。
- D3 系统上限：语言覆盖 + 结构化输出 + 系统版本；超限再自定义。

## 三、代码题：评分要点与提示

### Q1 Vision OCR
- 评分要点：程序化图片 + VNRecognizeTextRequest 实跑；识别文本与置信度打印。
- 参考答案要点：`VNImageRequestHandler` + 识别请求；`VNRecognizedTextObservation` 取 top candidate。

### Q2 VisionKit 骨架
- 评分要点：ImageAnalyzer/VKImageAnalysisRequest/Interaction 骨架完整；待真机标注诚实；请求类型清单打印。
- 参考答案要点：`ImageAnalyzer` + `ImageAnalysisInteraction` 挂在视图；标注 iOS 16+/App 环境。

### Q3 三选一决策 CLI
- 评分要点：输入场景 → 决策 + 理由（记账）；至少一处「先内建后升级」路径。
- 参考答案要点：if 语言覆盖不足 → 自定义；默认内建。

### Q4 权限与隐私清单
- 评分要点：清单项完整（权限/on-device/声明/生命周期）。
- 参考答案要点：打印检查项。

## 四、使用纪律
- 判分只认证据：Q1 实跑输出；Q2 待真机标注；决策记账。
- 失真自查：把骨架当实跑、没有记账就选型 = 该题作废重跑。
