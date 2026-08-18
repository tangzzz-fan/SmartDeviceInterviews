# T9-04 费曼草稿：C++ + Python + CoreML 集成（示例）

> **示例文件**：演示「脱稿重推 + 对照 + 60 秒讲稿」长什么样，**不是真实产物**。

## 一、五模型脱稿重推

- **M1 混合栈**：Python 造模、C++ 核心引擎、CoreML 端侧推理；三段靠数据契约连接。
- **M2 三条 C++ 路线**：C API（最稳、跨语言）、C++ API（类型安全）、ObjC++（贴 ObjC）；纯 C++ 引擎默认 C API。
- **M3 数据边界在特征转换**：MultiArray 步长、图像方向/内存、float16/32——三个坑都要显式处理。
- **M4 构建与打包**：链接 CoreML.framework、.mlmodelc 进资源、条件编译隔离。
- **M5 错误与线程**：MLModelGetPredictionError 取错；不可变模型并发安全。

## 二、对照表

| 路线 | 类型安全 | 跨语言 | 编译依赖 |
|------|---------|--------|---------|
| C API | 低 | 高（纯 C） | 稳 |
| C++ API | 高 | 中 | 随 Xcode |
| ObjC++ | 中 | 低 | 慢 |

## 三、一个例子讲到底

Python 造一个微型 MLP → `model.mlmodel` → `xcrun coremlcompiler compile` 出 `.mlmodelc` → C++ 用 C API 加载并推理 → 与 Python 对拍误差 1e-5。整条链真实跑通，「混合栈」不再是概念。

## 四、60 秒讲稿

「真实项目里 CoreML 很少是纯 Swift 独角戏：Python 负责造模，C++ 核心引擎负责跨平台和低延迟，CoreML 负责端侧推理。C++ 接 CoreML 三条路——C API 最稳也最能跨语言，纯 C++ 引擎默认它；数据转换有三个坑：MultiArray 步长、图像方向、float16 类型；构建要链 CoreML.framework、把 .mlmodelc 当资源、用条件编译隔离。能编译不等于能推理，对拍误差才是集成成功的证据。」

## 五、自检三问

1. 被问「C++ 接 CoreML 默认哪条路」能答（C API）。
2. 能讲给同事听：用了造模→编译→C++ 推理的例子。
3. 诚实自查：C3 的三个坑是我复攻补全的。
