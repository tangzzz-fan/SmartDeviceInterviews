# SmartDevice Interviews — API

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Health: http://127.0.0.1:8000/api/health

## Import content (manual sync)

`综合版/` Markdown is the source of truth. After editing materials, re-run:

```bash
cd backend
source .venv/bin/activate
# default: entire 综合版 (题库 + 清单 + 白板 + STAR + 英文 + 自评)
python -m app.import_content

# or a specific file
python -m app.import_content --path ../综合版/09_执行清单.md
python -m app.import_content --force
```

Import **upserts content by stable id** and **never overwrites** user progress
(checklist checks, scores, reflections, practice counts, skill snapshots, …).
