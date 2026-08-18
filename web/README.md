# SmartDevice Interviews — Web

React + Vite 前端。开发时通过 Vite 代理访问本机 FastAPI（`/api` → `http://127.0.0.1:8000`）。

完整操作说明见 [docs/LEARNING_TRACKER.md](../docs/LEARNING_TRACKER.md)。

## Setup

```bash
cd web
npm install
```

## Run

先启动后端并导入材料（见 [`../backend/README.md`](../backend/README.md)），再：

```bash
cd web
npm run dev
```

打开 http://127.0.0.1:5173 — 导航含题库 / 清单 / 白板 / STAR / 英文 / 自评 / 模拟面。
