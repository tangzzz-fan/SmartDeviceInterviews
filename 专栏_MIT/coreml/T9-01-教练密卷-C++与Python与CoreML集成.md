# T9-01 教练密卷：C++ + Python + CoreML 集成（仅教练分支/归档，学员禁阅）

> 本文件含弱/中/强三级提示、评分要点与参考答案。使用纪律：直接要答案 → 反问「C++ 拿到的输入是什么、形状顺序对了吗」。

## 一、概念题：提示梯与评分要点

### C1 完整数据流
- 弱提示：三段各产出什么（.mlmodel / .mlmodelc / 预测结果）？契约在哪段定义？
- 中提示：Python 转换时定义契约；coremlcompiler 编译不改变契约；C++ 按契约取数。
- 强提示：Python（训练+转换，定义名/型/形/预处理）→ coremlcompiler（编译优化，契约不变）→ C++（加载 .mlmodelc，按契约构造输入/解读输出）。
- 评分要点：真懂特征：三段产物 + 契约锚点；死记硬背典型：「转完直接丢给 C++。」
- 参考答案：契约在 Python 转换时钉死；编译与推理都不改契约。

### C2 C++ 集成路线取舍
- 弱提示：本机 SDK 的 CoreML 头文件里有什么（ObjC 为主，无 MLModel.hpp 与 C API）？那 C++ 怎么调？
- 中提示：ObjC++ 桥 = C++ 代码里调 MLModel ObjC API，用 -fobjc-arc 编译；C++ 引擎怎么隔离 CoreML 类型？
- 强提示：当前 SDK 实测路线 = ObjC++ 桥（MLModel + MLMultiArray + predictionFromFeatures:）；C++ 引擎包一层适配层（C++ 接口 + ObjC++ 实现），避免 CoreML 类型泄漏；旧 SDK 才有 C API，SDK 提供时可用 C++ API。
- 评分要点：真懂特征：知道当前 SDK 用 ObjC++ + 适配层隔离；死记硬背典型：「用 C API 就行。」
- 参考答案：当前 SDK 默认 ObjC++ 桥；C++ 引擎用适配层隔离；C API/C++ API 视 SDK 提供情况。

### C3 特征转换的坑
- 弱提示：MLMultiArray 的 stride/布局与 C++ 数组顺序；图像 buffer 的格式/方向；float16 vs float32——各是什么坑？
- 中提示：谁负责转换（C++ 侧），谁负责校验（契约）？
- 强提示：三坑：① MultiArray 步长（C 连续 vs 非连续）；② 图像 buffer 像素格式/方向/所有权；③ float16 与 float32 类型不匹配直接报错。规避：按契约显式转换 + 单元测试。
- 评分要点：真懂特征：三坑 + 规避；死记硬背典型：「直接 memcpy。」
- 参考答案：按契约构造 MLMultiArray/MLImage，类型/布局/方向显式处理，测试断言。

### C4 构建与打包
- 弱提示：链接什么框架？.mlmodelc 放哪？
- 中提示：跨平台代码怎么隔离（#if canImport(CoreML) / #if __APPLE__）？
- 强提示：链接 `-framework CoreML -framework Foundation`；.mlmodelc 作为 App 资源；`#if __APPLE__` 隔离 CoreML 依赖，非 Apple 平台走其他后端。
- 评分要点：真懂特征：链接 + 资源 + 条件编译；死记硬背典型：「C++ 项目不能接 CoreML。」
- 参考答案：CoreML.framework + Foundation；资源打包；条件编译隔离。

### C5 错误与线程
- 弱提示：ObjC API 的错误怎么拿（NSError 出参）？并发预测安全吗？
- 中提示：MLModel 实例不可变吗？prediction 上下文独立吗？
- 强提示：`modelWithContentsOfURL:error:` / `predictionFromFeatures:...error:` 用 NSError 出参；MLModel 不可变 → 并发预测安全（每次 prediction 独立）；模型对象生命周期由 ARC/持有者管理。
- 评分要点：真懂特征：NSError 出参 + 不可变模型并发安全；死记硬背典型：「ObjC 不能并发。」
- 参考答案：NSError 出参 + 不可变模型并发安全 + 生命周期由持有者管。

### C6 混合栈分工
- 弱提示：训练（Python）、引擎（C++）、推理（CoreML）各自失败模式是什么？
- 中提示：集成测试放哪（对拍）？
- 强提示：Python 管数据/训练/转换；C++ 管跨平台引擎与调度；CoreML 管端侧执行；集成测试 = 同一输入三端对拍。分工看「跨平台复用需求」。
- 评分要点：真懂特征：三段分工 + 失败模式 + 对拍；死记硬背典型：「能跑就是集成好了。」
- 参考答案：分工明确 + 对拍集成测试；跨平台复用是 C++ 的唯一理由。

## 二、争议焦点参考立场

- D1 路线：纯 C++ 引擎默认 C API；类型安全优先 C++ API；ObjC 生态用 ObjC++。
- D2 C++ 上 iOS：核心逻辑跨平台复用则 C++，否则 Swift 即可；按「复用需求」记账。
- D3 生成：本地脚本可复现 + CI 产物哈希校验；模型变更走版本号。

## 三、代码题：评分要点与提示

### Q1 Python 造 .mlmodel
- 评分要点：训练 + trace + convert + 保存成功；规格打印。
- 参考答案要点：同 T7 Q1 的简化版。

### Q2 编译 .mlmodelc
- 评分要点：coremlcompiler 编译成功；产物路径与内容打印。
- 参考答案要点：`xcrun coremlcompiler compile model.mlmodel out/`；`ls out/model.mlmodelc`。

### Q3 C++ 推理
- 评分要点：ObjC++ 加载 .mlmodelc + MLMultiArray 输入 + predictionFromFeatures: 预测 + 打印结果；编译运行成功；与 Python 对拍误差。
- 参考答案要点：`[MLModel modelWithContentsOfURL:error:]` → `MLMultiArray` 填值 → `predictionFromFeatures:options:error:` → 取 output；编译命令 `clang++ -x objective-c++ -std=c++17 -fobjc-arc -framework CoreML -framework Foundation`。

### Q4 集成报告
- 评分要点：检查清单 + 对拍误差 + Markdown 报告。
- 参考答案要点：见 Q3 结果 + 清单。

## 四、使用纪律
- 判分只认证据：对拍误差、编译运行输出、产物清单；「能编译」≠「推理成功」。
- 失真自查：没跑 C++ 就说通了、对拍没数字 = 该题作废重跑。
