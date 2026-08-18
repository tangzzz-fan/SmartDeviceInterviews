# T01 — Scaffold：本机打开站点并打通 health

**What to build:** `web/` + `backend/` 可启动；前端能请求到 `GET /api/health`；Vite 代理 `/api`；空库可迁移建表。

**Blocked by:** None — can start immediately

**Status:** done

## Acceptance criteria

- [x] `uvicorn` 与 `vite` 按 README 可启动
- [x] 浏览器可见 health 成功状态（或极简壳页）
- [x] SQLite 文件可创建，CORS/代理可用
