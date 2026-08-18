"""Upsert markdown content into SQLite without touching user progress."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.importing.parse_extras import (
    parse_checklist,
    parse_english,
    parse_skills,
    parse_star_stories,
    parse_whiteboards,
)
from app.importing.parse_questions import parse_questions_markdown
from app.models import (
    ChecklistItem,
    ChecklistProgress,
    ContentSource,
    EnglishProgress,
    EnglishScript,
    PracticeStatus,
    Question,
    QuestionProgress,
    QuestionStatus,
    SkillDimension,
    StarProgress,
    StarStory,
    Whiteboard,
    WhiteboardProgress,
)


@dataclass
class ImportReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "added": self.added,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "skipped_files": self.skipped_files,
            "errors": self.errors,
            "summary": {
                "added": len(self.added),
                "updated": len(self.updated),
                "unchanged": len(self.unchanged),
                "skipped_files": len(self.skipped_files),
                "errors": len(self.errors),
            },
        }


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _merge(into: ImportReport, part: ImportReport) -> None:
    into.added.extend(part.added)
    into.updated.extend(part.updated)
    into.unchanged.extend(part.unchanged)
    into.skipped_files.extend(part.skipped_files)
    into.errors.extend(part.errors)


def _touch_source(session: Session, rel_path: str, digest: str, entity_type: str) -> None:
    row = session.exec(select(ContentSource).where(ContentSource.path == rel_path)).first()
    now = datetime.utcnow()
    if row is None:
        session.add(
            ContentSource(
                path=rel_path,
                content_hash=digest,
                last_imported_at=now,
                entity_type=entity_type,
            )
        )
    else:
        row.content_hash = digest
        row.last_imported_at = now
        row.entity_type = entity_type
        session.add(row)


def _should_skip(session: Session, rel: str, digest: str, force: bool) -> bool:
    if force:
        return False
    existing = session.exec(select(ContentSource).where(ContentSource.path == rel)).first()
    return bool(existing and existing.content_hash == digest)


def _upsert_question(session: Session, parsed, report: ImportReport) -> None:
    existing = session.get(Question, parsed.id)
    now = datetime.utcnow()
    if existing is None:
        session.add(
            Question(
                id=parsed.id,
                module=parsed.module,
                priority=parsed.priority,
                title=parsed.title,
                answer_md=parsed.answer_md,
                followups_md=parsed.followups_md,
                tradeoffs_md=parsed.tradeoffs_md,
                source_path=parsed.source_path,
                orphaned=False,
                updated_at=now,
            )
        )
        if session.get(QuestionProgress, parsed.id) is None:
            session.add(QuestionProgress(question_id=parsed.id, status=QuestionStatus.todo))
        report.added.append(parsed.id)
        return

    changed = (
        existing.title != parsed.title
        or existing.module != parsed.module
        or existing.priority != parsed.priority
        or existing.answer_md != parsed.answer_md
        or existing.followups_md != parsed.followups_md
        or existing.tradeoffs_md != parsed.tradeoffs_md
        or existing.source_path != parsed.source_path
        or existing.orphaned
    )
    if not changed:
        report.unchanged.append(parsed.id)
        return

    existing.title = parsed.title
    existing.module = parsed.module
    existing.priority = parsed.priority
    existing.answer_md = parsed.answer_md
    existing.followups_md = parsed.followups_md
    existing.tradeoffs_md = parsed.tradeoffs_md
    existing.source_path = parsed.source_path
    existing.orphaned = False
    existing.updated_at = now
    session.add(existing)
    report.updated.append(parsed.id)


def import_question_file(
    session: Session,
    path: Path,
    *,
    repo_root: Path | None = None,
    force: bool = False,
) -> ImportReport:
    report = ImportReport()
    if not path.is_file():
        report.errors.append(f"not a file: {path}")
        return report

    try:
        rel = str(path.resolve().relative_to(repo_root.resolve())) if repo_root else str(path)
    except ValueError:
        rel = str(path)

    digest = file_hash(path)
    if _should_skip(session, rel, digest, force):
        report.skipped_files.append(rel)
        return report

    try:
        parsed_list = parse_questions_markdown(path, repo_relative=rel)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"{rel}: {exc}")
        return report

    if not parsed_list:
        report.errors.append(f"{rel}: no questions found")
        return report

    for parsed in parsed_list:
        _upsert_question(session, parsed, report)

    _touch_source(session, rel, digest, "question")
    session.commit()
    return report


def _generic_upsert(
    session: Session,
    *,
    model_cls,
    progress_cls,
    progress_fk: str,
    progress_defaults: dict,
    parsed_id: str,
    fields: dict,
    report: ImportReport,
) -> None:
    existing = session.get(model_cls, parsed_id)
    if existing is None:
        session.add(model_cls(id=parsed_id, **fields))
        if session.get(progress_cls, parsed_id) is None:
            session.add(progress_cls(**{progress_fk: parsed_id, **progress_defaults}))
        report.added.append(parsed_id)
        return

    changed = False
    for key, value in fields.items():
        if getattr(existing, key) != value:
            setattr(existing, key, value)
            changed = True
    if getattr(existing, "orphaned", False):
        existing.orphaned = False
        changed = True
    if changed:
        session.add(existing)
        report.updated.append(parsed_id)
    else:
        report.unchanged.append(parsed_id)


def import_extra_file(
    session: Session,
    path: Path,
    *,
    kind: str,
    repo_root: Path | None = None,
    force: bool = False,
) -> ImportReport:
    report = ImportReport()
    if not path.is_file():
        report.errors.append(f"not a file: {path}")
        return report

    try:
        rel = str(path.resolve().relative_to(repo_root.resolve())) if repo_root else str(path)
    except ValueError:
        rel = str(path)

    digest = file_hash(path)
    if _should_skip(session, rel, digest, force):
        report.skipped_files.append(rel)
        return report

    try:
        if kind == "checklist":
            parsed_list = parse_checklist(path, repo_relative=rel)
            for p in parsed_list:
                _generic_upsert(
                    session,
                    model_cls=ChecklistItem,
                    progress_cls=ChecklistProgress,
                    progress_fk="item_id",
                    progress_defaults={"checked": False},
                    parsed_id=p.id,
                    fields={
                        "day_key": p.day_key,
                        "day_title": p.day_title,
                        "sort_order": p.sort_order,
                        "text": p.text,
                        "source_path": p.source_path,
                        "orphaned": False,
                    },
                    report=report,
                )
        elif kind == "whiteboard":
            parsed_list = parse_whiteboards(path, repo_relative=rel)
            for p in parsed_list:
                _generic_upsert(
                    session,
                    model_cls=Whiteboard,
                    progress_cls=WhiteboardProgress,
                    progress_fk="whiteboard_id",
                    progress_defaults={"status": PracticeStatus.todo, "practiced_count": 0},
                    parsed_id=p.id,
                    fields={
                        "title": p.title,
                        "priority": p.priority,
                        "body_md": p.body_md,
                        "source_path": p.source_path,
                        "orphaned": False,
                    },
                    report=report,
                )
        elif kind == "star":
            parsed_list = parse_star_stories(path, repo_relative=rel)
            for p in parsed_list:
                _generic_upsert(
                    session,
                    model_cls=StarStory,
                    progress_cls=StarProgress,
                    progress_fk="story_id",
                    progress_defaults={"filled_real_numbers": False, "recited": False},
                    parsed_id=p.id,
                    fields={
                        "title": p.title,
                        "is_flagship": p.is_flagship,
                        "body_md": p.body_md,
                        "source_path": p.source_path,
                        "orphaned": False,
                    },
                    report=report,
                )
        elif kind == "english":
            parsed_list = parse_english(path, repo_relative=rel)
            for p in parsed_list:
                _generic_upsert(
                    session,
                    model_cls=EnglishScript,
                    progress_cls=EnglishProgress,
                    progress_fk="script_id",
                    progress_defaults={"practiced": False},
                    parsed_id=p.id,
                    fields={
                        "title": p.title,
                        "body_md": p.body_md,
                        "sort_order": p.sort_order,
                        "source_path": p.source_path,
                        "orphaned": False,
                    },
                    report=report,
                )
        elif kind == "skills":
            parsed_list = parse_skills(path, repo_relative=rel)
            for p in parsed_list:
                existing = session.get(SkillDimension, p.id)
                fields = {
                    "name": p.name,
                    "prompt": p.prompt,
                    "criterion": p.criterion,
                    "group_name": p.group_name,
                    "sort_order": p.sort_order,
                    "source_path": p.source_path,
                    "orphaned": False,
                }
                if existing is None:
                    session.add(SkillDimension(id=p.id, **fields))
                    report.added.append(p.id)
                else:
                    changed = any(getattr(existing, k) != v for k, v in fields.items())
                    if changed:
                        for k, v in fields.items():
                            setattr(existing, k, v)
                        session.add(existing)
                        report.updated.append(p.id)
                    else:
                        report.unchanged.append(p.id)
        else:
            report.errors.append(f"unknown kind: {kind}")
            return report
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"{rel}: {exc}")
        return report

    if not report.added and not report.updated and not report.unchanged and not report.errors:
        report.errors.append(f"{rel}: no items found")
        return report

    _touch_source(session, rel, digest, kind)
    session.commit()
    return report


def detect_kind(path: Path) -> str | None:
    name = path.name
    parent = path.parent.name
    if parent == "03_题库与答案" or path.match("*/03_题库与答案/*.md"):
        return "question"
    if name.startswith("09_") or "执行清单" in name:
        return "checklist"
    if name.startswith("05_") or "白板" in name:
        return "whiteboard"
    if name.startswith("06_") or "STAR" in name:
        return "star"
    if name.startswith("07_") or "英文" in name:
        return "english"
    if name.startswith("02_") or "差距" in name:
        return "skills"
    return None


def import_paths(
    session: Session,
    paths: list[Path],
    *,
    repo_root: Path | None = None,
    force: bool = False,
) -> ImportReport:
    merged = ImportReport()
    for path in paths:
        if path.is_dir():
            files = sorted(path.rglob("*.md")) if path.name != "03_题库与答案" else sorted(path.glob("*.md"))
            # For 综合版 root, import known files
            if path.name == "综合版":
                files = [
                    path / "03_题库与答案",
                    path / "09_执行清单.md",
                    path / "05_白板图解.md",
                    path / "06_STAR故事库.md",
                    path / "07_英文与跨团队沟通.md",
                    path / "02_差距地图与补强策略.md",
                ]
                for item in files:
                    part = import_paths(session, [item], repo_root=repo_root, force=force)
                    _merge(merged, part)
                continue
            if not files and path.name != "03_题库与答案":
                # directory of md
                files = sorted(path.glob("*.md"))
            for file in files:
                if file.is_dir():
                    part = import_paths(session, [file], repo_root=repo_root, force=force)
                else:
                    kind = detect_kind(file)
                    if kind == "question":
                        part = import_question_file(session, file, repo_root=repo_root, force=force)
                    elif kind:
                        part = import_extra_file(session, file, kind=kind, repo_root=repo_root, force=force)
                    else:
                        part = ImportReport(errors=[f"unsupported: {file}"])
                _merge(merged, part)
        else:
            kind = detect_kind(path)
            if kind == "question":
                part = import_question_file(session, path, repo_root=repo_root, force=force)
            elif kind:
                part = import_extra_file(session, path, kind=kind, repo_root=repo_root, force=force)
            else:
                part = ImportReport(errors=[f"unsupported: {path}"])
            _merge(merged, part)
    return merged
