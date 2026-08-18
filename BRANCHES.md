# 分支约定

| 分支 | 内容 |
| --- | --- |
| **`main`** | 知识库：`综合版/`、`专栏_*`、`labs/`、源材料归档。不含 `web/` / `backend/`。 |
| **`webapp`** | 学习站全量：在知识库之上叠加 React + FastAPI、导入 CLI、练习 API。 |

工作流建议：

1. 改面试 Markdown / labs → 提交到 `main` 并推送。
2. 改学习站代码 → 在 `webapp` 上开发；定期 `git merge main` 同步知识库。
3. 不要把 `web/`、`backend/` 再合回 `main`。
