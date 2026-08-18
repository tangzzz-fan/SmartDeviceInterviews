# T7-01 教练密卷：Python 模型创建与转换（仅教练分支/归档，学员禁阅）

> 本文件含弱/中/强三级提示、评分要点与参考答案。使用纪律：直接要答案 → 反问「转换的输入是什么」。

## 一、概念题：提示梯与评分要点

### C1 转换的输入与 trace
- 弱提示：PyTorch 导出有两个名字：TorchScript 与 trace——转换器要哪个？为什么需要输入样例？
- 中提示：trace 是「跑一遍记录数据流」，所以需要 dummy input；不带它转不了。
- 强提示：`traced = torch.jit.trace(model, example)`；coremltools.convert 接受 traced/ScriptModule/TorchScript 文件；TF 侧用 SavedModel。trace 不读源码，所以动态控制流会丢。
- 评分要点：真懂特征：trace 机制 + 需要样例的原因 + TF 对照；死记硬背典型：「convert(model) 就行。」
- 参考答案：输入 = torch.jit.trace 产物（含样例）；trace 记录数据流，动态分支需 scripting；TF 用 SavedModel。

### C2 NeuralNetwork vs ML Program
- 弱提示：新规范叫什么？老规范叫什么？各自强在哪？
- 中提示：ML Program 是 coremltools 6+ 的默认输出吗？可更新性谁好？
- 强提示：ML Program：新算子、性能好、可更新、工具链新；NeuralNetwork：兼容老模型/老工具。新项目默认 ML Program（`convert_to="mlprogram"`）。
- 评分要点：真懂特征：两者差异 + 新项目默认；死记硬背典型：「都一样。」
- 参考答案：默认 ML Program；旧模型/老工具链才用 NeuralNetwork。

### C3 端侧回归的必要性
- 弱提示：转换会改什么（算子/精度/数值顺序）？T2 C3 的「三个不等」还记得吗？
- 中提示：Python 99% 是「分布内+原框架」；端侧是「设备分布+CoreML」。
- 强提示：转换有损 + 设备分布不同 + 度量环境不同 → 必须端侧回归（真实设备/样本）后才可引用数字。
- 评分要点：真懂特征：转换有损 + 与 T2 C3 呼应；死记硬背典型：「转换是无损的。」
- 参考答案：转换可能改算子/精度；端侧回归是引用数字的前提。

### C4 量化流程与验收
- 弱提示：量化有几种（fp16/int8/palettization）？各换什么？
- 中提示：流程：转换 → 量化 → 端侧回归 → 三指标（体积/延迟/任务指标）对比。
- 强提示：fp16 无损但省一半体积；int8/palettization 有损换体积与速度；验收 = 三指标账本，掉点超阈值即否。
- 评分要点：真懂特征：流程 + 三指标验收；只报体积 = 半过。
- 参考答案：fp16 默认；int8/palettization 按账本；验收三指标。

### C5 契约定义与对齐
- 弱提示：契约要素有哪些（名/型/形/预处理/标签）？Python 转换时在哪声明？
- 中提示：`ct.convert` 的 inputs/outputs 参数、模型描述、预处理可内嵌吗？
- 强提示：转换脚本里用 `inputs=[ct.TensorType(name:shape:)]` 等声明；预处理（归一化）要作为模型的一部分或文档化；Swift 端按同一契约校验。
- 评分要点：真懂特征：契约要素 + Python 声明位置 + Swift 校验；死记硬背典型：「转出来就能用。」
- 参考答案：转换时声明输入输出类型/形状；预处理必须钉死并文档化；Swift 端适配层校验。

### C6 版本管理
- 弱提示：二进制入库的问题（体积/diff）？可复现脚本怎么保证可复现？
- 中提示：标签表/预处理版本与模型不同步会怎样（静默错类）？
- 强提示：推荐：可复现脚本 + 版本号 + 产物哈希（CI 构建）；标签表与预处理版本与模型同版本发布；回顾 T2 C5。
- 评分要点：真懂特征：脚本+哈希方案 + 版本同步；死记硬背典型：「把 .mlmodel 提交到 git 就行。」
- 参考答案：脚本 + 版本 + 哈希；标签/预处理与模型同版本。

## 二、争议焦点参考立场

- D1 转换 vs 重训：先转换拿基线，端侧回归不达标再评估端侧友好重训。
- D2 量化档位：算法与客户端各有一票；量化账本为共同依据。
- D3 .mlmodel 进 git：优先脚本 + 哈希；小模型可整包入库但要接受体积。

## 三、代码题：评分要点与提示

### Q1 微型分类器 → CoreML
- 评分要点：训练跑通；trace + convert 成功；`model.mlmodel` 保存；规格打印（输入/输出名/型/形）。
- 参考答案要点：`torch.jit.trace` → `ct.convert(traced, inputs=[ct.TensorType(shape=(1,4))])` → `mlmodel.save(...)`（mlprogram → `.mlpackage`）；`mlmodel.get_spec()` 打印。

### Q2 对拍
- 评分要点：torch 与 CoreML 同一输入输出比较；最大绝对误差与 Top1 一致性打印。
- 参考答案要点：两边 `softmax` 后比较；误差 < 1e-5 且 Top1 一致。

### Q3 量化对比
- 评分要点：fp16（及可选 int8/palettization）转换；体积对比；Top1 一致性；值得/不值得结论。
- 参考答案要点：`ct.models.neural_network.quantization_utils.quantize_weights`（或 mlprogram 量化）；账本输出。

### Q4 契约清单
- 评分要点：名/型/形/预处理/标签/版本三元组全打印。
- 参考答案要点：从 `get_spec()` 提取 + 文档字段。

## 四、使用纪律
- 判分只认证据：对拍误差、体积数字、规格输出；「感觉没问题」不算。
- 失真自查：没跑 torch 就说通了、对拍没有数字 = 该题作废重跑。
