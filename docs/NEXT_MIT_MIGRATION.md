# 计划：提交 + 合并 MIT-Migration

## 1. 提交（push）

当前 `algo-lab` / `webapp` 工作区干净 → 推送到 `origin`（此前未 push）。

## 2. MIT-Migration 合并（分支 `mit-migration` ← `algo-lab`）

**源目录事实核对**（`/Users/apple/Developments/MIT-Migration`）：

| 轨道 | 源状态 | 本仓动作 |
| --- | --- | --- |
| Swift | `MIT-Swift-migration/` 完整（T1–T4 四件套 + `代码/`） | → `专栏_MIT/swift/` + `labs/mit-swift-migration/代码/` |
| Python | `MIT-Python-Migration/` 仅 `.gitkeep` | → `专栏_MIT/python/README.md` 标明占位 |
| CoreML / Design Pattern | **源目录中不存在** | README 写明；CoreML 学习指向已有 `专栏_AlgoLab` / lab-docs，不擅自拷贝外部书稿 |

**交付**

- `专栏_MIT/README.md` + 导入 `/column/mit`
- 导航增加 **MIT**
- ticket T17 + 计划文档勾选
- commit（+ push，与步骤 1 一致）

## 验收

- [x] `algo-lab` / `webapp` 已 push 到 origin
- [x] `专栏_MIT/swift/` 导入 22 篇；`/column/mit` 可浏览
- [x] `labs/mit-swift-migration/代码/` 含 T1–T4
- [x] README 如实记录 Python 空、CoreML/Design Pattern 不在源目录
