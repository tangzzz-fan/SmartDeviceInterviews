---
title: "T3 教练出题集：Vision 与媒体管线"
date: 2026-08-17
---

# T3 教练出题集：Vision 与媒体管线

## 一、共识五模型

| # | 模型 | 一句话 |
|---|------|--------|
| M1 | Vision 是编排层 | 请求队列、裁剪、方向、缩放；CoreML 是其中一种 handler |
| M2 | 预处理即模型的一部分 | 训练时做什么，推理就必须对齐，否则准头静默崩 |
| M3 | 方向是一等公民 | EXIF/UIImage.orientation 搞错 = 类别全错 |
| M4 | 内建 vs 自定义 | 系统模型省体积；自定义换控制权 |
| M5 | 异步与生命周期 | VNRequest 完成回调线程不安全假设；要回主线程更新 UI |

## 二、争议三焦点

**D1 所有图像模型是否都应包一层 Vision？**  
**D2 该不该在 App 里做 test-time augmentation？**  
**D3 批处理 vs 单张：产品体验优先还是吞吐优先？**

## 三、概念题（6）

C1 Vision 与 CoreML 的分工？  
C2 列出图像预处理检查清单（≥5 项）。  
C3 orientation 错了会出现什么现象？如何验证？  
C4 何时用 VNClassifyImageRequest，何时上自定义模型？  
C5 回调线程问题：UI 更新该怎么做？  
C6 给「扫证件」场景写端侧/云/内建三选一账。

## 四、代码题（4）

Q1 生成一张程序化 CGImage，跑 VNClassifyImageRequest，打印 Top3。  
Q2 打印 orientation 枚举与「错误方向会怎样」说明。  
Q3 VNCoreMLModel 加载失败时的错误处理骨架（无真实模型也可演示编译 API）。  
Q4 管线伪时序：记录 preprocess / infer / postprocess 三段耗时（可用 sleep 模拟）。
