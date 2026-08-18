# 智能穿戴设备算法落地· 项目导航

这个仓库用于沉淀 AI + iOS + 算法工程化相关实践与资料。  
如果你是第一次接触本仓库，建议先从 `algo-engineering-lab` 开始。

---

## 仓库包含什么

- `algo-engineering-lab/`：算法工程化验证项目（Python 原型 → golden → C/Swift parity）
- `Talk with K3/`：岗位分析、面试准备与过程记录文档

---

## 1 分钟上手（推荐）

```bash
cd algo-engineering-lab
uv sync
swift test --filter ParityTests
```

如果测试全绿，说明你本地已经跑通核心链路。

---

## 新人应该先看哪些文档

1. `algo-engineering-lab/README.md`（项目目标、环境要求、Case 导航）
2. `algo-engineering-lab/tickets.md`（任务拆解与完成状态）
3. `algo-engineering-lab/docs/01-数值一致性规范.md`
4. `algo-engineering-lab/docs/03-黄金数据集规范.md`
5. `algo-engineering-lab/docs/04-C库集成规范.md`

---

## 常用命令

```bash
# 进入项目
cd algo-engineering-lab

# Python 环境
uv sync

# 跑 parity（核心回归）
swift test --filter ParityTests

# 重生指定 golden（示例）
uv run python -m python.generate_golden hrv_time_domain
uv run python -m python.generate_golden fir_ppg
uv run python -m python.generate_golden hrv_freq_domain
uv run python -m python.generate_golden coreml_quant
uv run python -m python.generate_golden streaming_fir
```

---

## 可扩展案例（下一步做什么）

为了便于持续迭代，这里已经整理好一份扩展路线图：

- `algo-engineering-lab/docs/08-扩展案例建议.md`

建议优先顺序：

1. HRV 伪差校正（快速增强算法鲁棒性）
2. OTA/DFU 断点续传状态机仿真（强贴合岗位）
3. 多通道同步与时间戳漂移校正（提升 BLE+算法联动深度）

每个候选案例都包含：

- 目标问题（为什么做）
- 实现范围（Python/C/Swift/golden）
- 验收标准（怎么判断做成）
- 面试价值（如何转成可讲述故事）

---

## 说明

- 本仓库中的 `algo-engineering-lab` 是**验证性原型**，用于方法验证与面试展示，不是生产医疗产品。
- 文档与代码保持同步更新；新增实现前，先补对应规范与对齐口径。
