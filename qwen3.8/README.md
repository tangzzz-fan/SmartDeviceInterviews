# Nirva Founding iOS Engineer 面试冲刺材料（Qwen3.8）

> 基于根目录 `README.md` 中的 JD 定制，目标岗位：Nirva 国内团队创始 iOS 工程师（AI 可穿戴产品）。

## 材料地图

| 目录 | 内容 | 用途 |
|------|------|------|
| `01-jd-analysis/` | JD 逐条拆解：考点、权重、风险点与对策 | 明确"为什么考、考什么、怎么答" |
| `02-sprint-plan/` | 7 天冲刺计划（按天、按模块、含自检清单） | 执行节奏与验收标准 |
| `03-question-bank/` | 七大模块题库（约 78 题，含考察意图/难度/追问） | 纯净题库，可反复自测 |
| `04-mock-interview/` | 2 轮模拟面试脚本（技术深挖轮 + 行为文化轮） | 全真演练 |
| `05-answers/` | 资深候选人 agent 生成的参考答案 | 对照学习答题结构与深度 |

## 题库模块一览（03-question-bank）

1. `ios-architecture.md` — Swift / 并发 / 内存 / 生命周期 / 架构设计 / 模块化
2. `ble-corebluetooth.md` — Core Bluetooth、配对、连接管理、OTA、异常恢复
3. `performance-infra.md` — 启动 / 内存 / 功耗 / 后台 / 稳定性 / CI/CD / 监控
4. `hw-sw-collaboration.md` — 软硬件联调、协议定义、EVT/DVT/PVT 流程
5. `ai-native.md` — AI 融入编码 / 调试 / 测试 / 文档 / 协作的实际做法
6. `behavioral.md` — Ownership、从 0 到 1、英文协作场景、行为面试
7. `bonus-topics.md` — 加分项专项：低功耗深挖 / OTA 进阶 / 离线同步一致性 / 音频采集 / 传感器数据 / C/C++ 与嵌入式 / 量产交付

## 使用方式

1. 先读 `01-jd-analysis/jd-breakdown.md`，建立全局认知。
2. 按 `02-sprint-plan/sprint-plan.md` 逐天推进，每天完成自检清单。
3. 用题库自测：遮住 `05-answers/`，口头作答后再对照参考答案。
4. Day7 用 `04-mock-interview/mock-interview.md` 做全真模拟。
5. 需要新题的答案时，调用 `senior-candidate` 子代理生成。

## 资深候选人 agent

- 名称：`senior-candidate`（Qoder 子代理）
- 人设：8 年+ iOS 经验、主导过可穿戴/IoT 产品 BLE 全链路与 OTA、熟悉性能调优与 CI/CD 建设、AI-native 工作方式、英文流利
- 答题风格：结论先行 + 原理 + 实战案例 + 边界情况
- 调用方式：在对话中要求使用 senior-candidate 子代理解答 `03-question-bank/` 中的题目
