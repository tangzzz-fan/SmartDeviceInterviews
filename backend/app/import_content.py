"""CLI: import markdown content into SQLite (preserves progress by id)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlmodel import Session

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import engine, init_db  # noqa: E402
from app import models  # noqa: F401, E402
from app.importing import import_paths  # noqa: E402


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import 综合版 markdown into SQLite")
    parser.add_argument(
        "--path",
        type=Path,
        action="append",
        dest="paths",
        help="Markdown file or directory (repeatable). Default: 综合版 (questions + extras)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root for relative source_path (default: parent of backend/)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-parse even if content hash is unchanged",
    )
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or default_repo_root()).resolve()
    paths = args.paths
    if not paths:
        paths = [repo_root / "综合版"]
        glass = repo_root / "专栏_SmartGlass"
        if glass.is_dir():
            paths.append(glass)

    init_db()
    with Session(engine) as session:
        report = import_paths(session, paths, repo_root=repo_root, force=args.force)

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
