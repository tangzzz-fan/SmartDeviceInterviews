"""Import 专栏_* markdown docs (e.g. SmartGlass column)."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.importing.report import ImportReport
from app.models import ColumnDoc, ContentSource

TITLE_FROM_H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def parse_column_title(path: Path, text: str) -> str:
    match = TITLE_FROM_H1.search(text)
    if match:
        return match.group(1).strip()
    return path.stem


def import_column_dir(
    session: Session,
    path: Path,
    *,
    column_key: str,
    repo_root: Path | None = None,
    force: bool = False,
) -> ImportReport:
    report = ImportReport()
    if not path.is_dir():
        report.errors.append(f"not a directory: {path}")
        return report

    files = sorted(path.glob("*.md"))
    if not files:
        report.errors.append(f"no markdown in {path}")
        return report

    for idx, file in enumerate(files):
        try:
            rel = (
                str(file.resolve().relative_to(repo_root.resolve()))
                if repo_root
                else str(file)
            )
        except ValueError:
            rel = str(file)

        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        existing_source = session.exec(
            select(ContentSource).where(ContentSource.path == rel)
        ).first()
        if existing_source and existing_source.content_hash == digest and not force:
            report.skipped_files.append(rel)
            continue

        text = file.read_text(encoding="utf-8")
        title = parse_column_title(file, text)
        doc_id = f"{column_key}:{file.stem}"

        existing = session.get(ColumnDoc, doc_id)
        fields = {
            "column_key": column_key,
            "title": title,
            "filename": file.name,
            "body_md": text,
            "sort_order": idx,
            "source_path": rel,
            "orphaned": False,
            "updated_at": datetime.utcnow(),
        }
        if existing is None:
            session.add(ColumnDoc(id=doc_id, **fields))
            report.added.append(doc_id)
        else:
            changed = any(
                getattr(existing, k) != v for k, v in fields.items() if k != "updated_at"
            )
            if changed:
                for k, v in fields.items():
                    setattr(existing, k, v)
                session.add(existing)
                report.updated.append(doc_id)
            else:
                report.unchanged.append(doc_id)

        now = datetime.utcnow()
        if existing_source is None:
            session.add(
                ContentSource(
                    path=rel,
                    content_hash=digest,
                    last_imported_at=now,
                    entity_type=f"column:{column_key}",
                )
            )
        else:
            existing_source.content_hash = digest
            existing_source.last_imported_at = now
            existing_source.entity_type = f"column:{column_key}"
            session.add(existing_source)

    session.commit()
    return report
