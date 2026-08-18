# 学习进度网站 · 使用与同步说明

React + Vite 前端 + FastAPI + SQLite 后端，把 [综合版](../综合版/) 面试材料变成可刷题、可打勾、可评分的本地学习站。

## 快速启动

```bash
# 1) 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2) 导入综合版材料（另开终端亦可）
cd backend && source .venv/bin/activate
python -m app.import_content

# 3) 前端
cd web
npm install
npm run dev
```

打开 http://127.0.0.1:5173  

- API 文档：http://127.0.0.1:8000/docs  
- Health：http://127.0.0.1:8000/api/health  

更细的后端说明见 [backend/README.md](../backend/README.md)，前端见 [web/README.md](../web/README.md)。

## 功能地图

| 页面 | 用途 |
| --- | --- |
| 概览 | 题库进度、模块完成率、最近模拟面 |
| 题库 | 70 题刷题（先题后答案）、状态/评分/笔记 |
| 清单 | D1–D7 + 面试前 24h 打勾、每日复盘 |
| 白板 | 白板 1–8 练习次数 |
| STAR | S1–S13 真实数字 / 脱稿 |
| 英文 | 脚本练习勾选 + 文字备注 |
| 自评 | 九维 + 加分项，D1/D7 双快照 |
| 模拟面 | 按 R1/R2/电话筛模板打分，通过判定 |
| 费曼 | 五层盲答 → 对照题库答案 |
| 西蒙 | 目标树节点自评 |
| 口述 | Glass 模式关闭口述，映射 Nirva 题/白板 |
| Glass / Algo / MIT | 独立专栏（SmartGlass / AlgoLab / MIT Migration） |

## 内容同步（改 Markdown 之后）

**原则**：`综合版/` 是 Nirva 主线 Source of Truth；`专栏_*` 是分栏材料；数据库是内容缓存 + 你的进度。改材料后不会自动进站，需手动导入。

```bash
cd backend && source .venv/bin/activate
python -m app.import_content          # 默认同步 综合版/ + 所有 专栏_*/
python -m app.import_content --force  # 忽略 hash，强制重解析
python -m app.import_content --path ../综合版/03_题库与答案/02-ble与corebluetooth.md
```

| 你改了什么 | 导入行为 | 进度 |
| --- | --- | --- |
| 已有题目正文（同 ID，如 A1） | upsert 内容 | **保留** status/score/notes |
| 同文件新增题目（新 ID） | insert 新题 | 旧进度不动 |
| 新增 `.md` 文件 | 放入已知目录并符合标题格式后导入 | 新条目默认未开始 |
| `专栏_*/**/*.md` | upsert `column_key:相对路径` | 与题库进度无关 |
| 清单勾选项文案 | 按稳定 id `checklist:D3:2` 更新文案 | 尽量保留已勾 |
| 删除 / 改 ID | 不自动删进度；内容可能 orphan | 进度仍在 |

### 新文件 / 新题约定

- **题库**：放在 `综合版/03_题库与答案/`，标题形如 `## A13. 标题` 或 `## AI7. …`
- **技术题小节优先用 `**答案**：` / `**追问应对**：` / `**取舍**：`
- **行为题**：可用 `**要点**：` / `**示范骨架**：` 等，导入器会归入答案区
- **清单**：`- [ ]` 项；天标题 `## D3：…`；稳定 id 按「当天第 N 个勾选」生成
- **白板**：`## 白板 3：标题`
- **STAR**：`## S4. 标题` 或加分项行 `- **S11 主题**：…`

文件 hash 未变时会跳过解析（报告里 `skipped_files`）。改完务必再跑 CLI，然后刷新浏览器。

## 模拟面通过标准

对齐 `综合版/08_模拟面试脚本.md`：

- 每题 1–5 分
- **通过**：已评分项的平均分 ≥ 4，且 **没有** 单题 ≤ 2

## 数据位置

- SQLite：`backend/data/app.db`（已 gitignore）
- 虚拟环境：`backend/.venv/`
- Tickets（Matt Pocock to-tickets）：`.scratch/interview-learning-tracker/issues/`

## 开发代理

Vite 将 `/api` 代理到 `http://127.0.0.1:8000`（见 `web/vite.config.ts`）。请先起后端再开前端。
