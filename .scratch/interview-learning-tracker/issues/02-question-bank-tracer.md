# T02 — 题库 tracer：单文件导入 → 刷题 → 进度持久 → 手动重导保留进度

**What to build:** 从 `01-ios核心.md` 导入 A1–A12；列表 + 先题后答案；标记 reviewed/recited + 评分笔记；再次跑 import CLI 改答案后进度仍在；导入报告可见。

**Blocked by:** T01

**Status:** done

## Acceptance criteria

- [x] CLI 能导入该文件并 upsert by `A1`…
- [x] 刷题页可揭晓答案并保存进度
- [x] 修改 MD 后重跑 CLI：内容更新、进度保留
- [x] 同文件新增 `A13` 再导入：新题出现且旧进度不动
