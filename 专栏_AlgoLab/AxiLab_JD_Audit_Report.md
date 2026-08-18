# AxiLab JD 落地审核报告

> 唯一事实真相：`JD.md`  
> 审核对象：`iOS_Interview_Prep/*` + `iOS_Senior_IoT_BLE_Review_Guide.md`  
> 视角：资深 iOS / BLE + 算法落地  
> 日期：2026-07-28 · **材料已按本报告后续意见完成一轮更新**（含 Core ML 加强版）

---

## 总判

| 维度 | 评分 |
| :--- | :--- |
| JD 知识点覆盖 | B+ |
| 落地工程可信度（原材料） | C+ → 更新后提升中 |
| 神经调节专项（原材料） | D → 已补模块 10 |
| P0 落地风险项 | 7（仍需入职后验证） |

材料作为面试备战包质量中上：OTA/BLE/健康数据/崩溃监控与 JD 条目基本对齐。原版多处把「面试可答」写成「生产可做」，且忽略神经调节与既有代码演进。这些已在分册中纠偏/补齐；**Core ML 按你的要求权重不降并加强落地深度**。

---

## 一、JD 职责 → 材料覆盖

| JD 职责 | 权重 | 覆盖 | 缺口 / 状态 |
| :--- | :--- | :--- | :--- |
| 主导 OTA/DFU | 核心 | 强 | 已纠正「BGTask 续传」误导；主路径改为 Bootloader 续传 |
| BLE 吞吐 / 重连 / 波形 | 核心 | 强 | 已注明 L2CAP 非默认 DFU；吞吐公式仅面试用 |
| FW / 算法联调 + Protobuf | 核心 | 中上 | 已补协议版本握手 / 在野兼容（模块 05） |
| 健康数据计算 / 存储 / 图表 | 核心 | 强 | 已补存储分层 TTL（模块 08） |
| 崩溃 / 日志 / 监控 | 明确要求 | 强 | 已修正 Signal Handler；补 OTA 漏斗 APM |
| 既有代码架构演进 | 明确要求 | 原弱 → 已补 | 新模块 11 Brownfield |
| 神经调节产品语境 | 公司定位 | 原无 → 已补 | 新模块 10 |
| Core ML / 算法实现 | **备战主线（不降权）** | 已加强 | 模块 03 端到端管线 + 黄金集 + 练习 |

---

## 二、原材料技术可信度问题（已处理）

1. **BGTaskScheduler 杀 App 后续 DFU** — 不可靠；改为 Bootloader 自恢复 + 断点续传。  
2. **L2CAP CoC 当默认 OTA** — 多数商用 DFU 仍走 GATT。  
3. **吞吐公式理想化** — 面试可讲，立项不可当预算。  
4. **RSA / ECDSA 混用** — 分册统一以 ECDSA P-256 + AES-GCM 为口径。  
5. **Signal Handler 示例自相矛盾** — 已拆正误示范。  
6. **Timer(0.004) 假装 250Hz** — 改为 chunk 回放。

---

## 三、从 JD 反推的真实落地风险

### P0
- 远程工程师无稳定硬件通路（Mock 盖不住 RF / Flash 时序）
- OTA 变砖与售后成本（Single-Bank、擦除超时、MAC+1、杀 App）
- 神经调节控制安全闭环（刺激限幅 / 确认 / Fail-Safe）
- 协议与在野设备兼容（无版本握手会静默错解析）

### P1
- 实时波形 vs iOS 后台存活
- 算力归属不清（MCU vs 手机 vs 云）
- 原始波形存储爆炸（需 TTL 分层）
- Brownfield 与交付并行（需 Flag + 硬件回归矩阵）

### P2
- 合规与 medical claim 边界
- 可观测性要服务联调（OTA 漏斗、Reason Code、proto 版本分布）

---

## 四、算法 / Core ML（权重不降）

JD 职位含「算法实现」。落地难在契约与回归，不在 API 背诵：

1. 与算法会签 I/O 契约（采样率、窗口、归一化、置信度）
2. `coremltools` → 预编译 → Actor + 零拷贝滑动窗口
3. 黄金集对齐 Python 参考
4. 选型：Core ML / TFLite C++ / Accelerate 按场景

详见：`iOS_Interview_Prep/03_CoreML_OnDevice_AI.md`

---

## 五、入职前 30 天剧本

**Week 0–1 必问**  
Flash Dual/Single-Bank？DFU 协议栈？Bootloader 是否改 MAC/UUID？刺激指令与互锁？波形采样与压缩？远程如何拿板 / PacketLogger？

**Week 1–2**  
OTA FSM + Guardian、重发现、协议握手、OTA 漏斗埋点、Mock + 黄金包；同步推进 Core ML 最小可演示链路。

**Week 2–4**  
Protocol 隔离 BLE；新 OTA 旁路 + Feature Flag；每 Sprint 跑硬件回归表。

---

## 六、备战材料现状（更新后）

| 动作 | 内容 |
| :--- | :--- |
| 加强 | 模块 03 Core ML 落地全链路 |
| 新建 | 10 神经调节安全、11 Brownfield |
| 纠偏 | 02 OTA、01 L2CAP、09 Signal、06 Mock |
| 补齐 | 05 协议兼容、08 存储分层、09 OTA 漏斗、06 远程联调 |
| 表达 | 07 增 Q9/Q10 + Core ML STAR |

入口：`iOS_Interview_Prep/00_README.md`

---

## 七、面试主叙事（对齐 JD）

**OTA 可靠性 → BLE 波形 → 算法落地（Core ML）→ 协议定责 → 健康可视化 → 安全/监控 → 旧代码演进**

反问清单见 README 第四节。
