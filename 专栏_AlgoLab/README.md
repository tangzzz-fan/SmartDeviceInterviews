# 专栏 · AlgoLab

来源：父目录 `algo_lab`（AxiLab / 智能穿戴算法工程化）。**独立栏目，不与 Nirva `A1` 混 ID。**

## 建议阅读顺序

| 步 | 分区 | 路径 |
| --- | --- | --- |
| 1 | 导读与 JD | `README` → `00_仓库导航` → `JD` / 审计报告 |
| 2 | 面试 Prep | `prep/00_README` → `prep/01`…（BLE / OTA / CoreML…） |
| 3 | Lab 规范与口径 | `lab-docs/01`…`05`、`02-算法对齐口径/*` |
| 4 | 实验复盘 | `lab-docs/06-实验复盘/case-*` |
| 5 | CoreML 入门 | `lab-docs/09-CoreML入门/*` |
| 6 | 岗位笔记 | `talk-k3/*`（按需） |

## 可运行代码

精简副本：`labs/algo-engineering-lab/`（已排除 `.build` / `.venv`）。

```bash
cd labs/algo-engineering-lab
uv sync
swift test --filter ParityTests
```

站内：`/column/algolab` · 总览 `/columns`。
