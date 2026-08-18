from datetime import datetime
from pathlib import Path
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.import_content import default_repo_root
from app.importing import import_paths
from app.models import Question, QuestionProgress, QuestionStatus
from app.schemas import (
    ImportRequest,
    QuestionDetail,
    QuestionListItem,
    QuestionProgressUpdate,
)

router = APIRouter(tags=["questions"])


def _question_sort_key(qid: str) -> tuple[str, int]:
    match = re.match(r"^([A-Za-z]+)(\d+)$", qid)
    if match:
        return match.group(1), int(match.group(2))
    return qid, 0


def _progress_map(session: Session, ids: list[str]) -> dict[str, QuestionProgress]:
    if not ids:
        return {}
    rows = session.exec(select(QuestionProgress).where(QuestionProgress.question_id.in_(ids))).all()
    return {row.question_id: row for row in rows}


@router.get("/questions", response_model=list[QuestionListItem])
def list_questions(
    module: str | None = None,
    priority: str | None = None,
    status: QuestionStatus | None = None,
    session: Session = Depends(get_session),
) -> list[QuestionListItem]:
    stmt = select(Question).where(Question.orphaned == False)  # noqa: E712
    if module:
        stmt = stmt.where(Question.module == module)
    if priority:
        stmt = stmt.where(Question.priority == priority)
    questions = list(session.exec(stmt).all())
    questions.sort(key=lambda q: _question_sort_key(q.id))
    progress = _progress_map(session, [q.id for q in questions])

    items: list[QuestionListItem] = []
    for q in questions:
        p = progress.get(q.id)
        st = p.status if p else QuestionStatus.todo
        if status is not None and st != status:
            continue
        items.append(
            QuestionListItem(
                id=q.id,
                module=q.module,
                priority=q.priority,
                title=q.title,
                status=st,
                score=p.score if p else None,
                last_practiced_at=p.last_practiced_at if p else None,
                orphaned=q.orphaned,
            )
        )
    return items


@router.get("/questions/{question_id}", response_model=QuestionDetail)
def get_question(question_id: str, session: Session = Depends(get_session)) -> QuestionDetail:
    q = session.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")
    p = session.get(QuestionProgress, question_id)
    return QuestionDetail(
        id=q.id,
        module=q.module,
        priority=q.priority,
        title=q.title,
        answer_md=q.answer_md,
        followups_md=q.followups_md,
        tradeoffs_md=q.tradeoffs_md,
        source_path=q.source_path,
        orphaned=q.orphaned,
        status=p.status if p else QuestionStatus.todo,
        score=p.score if p else None,
        notes=p.notes if p else "",
        last_practiced_at=p.last_practiced_at if p else None,
    )


@router.patch("/progress/questions/{question_id}", response_model=QuestionDetail)
def update_progress(
    question_id: str,
    body: QuestionProgressUpdate,
    session: Session = Depends(get_session),
) -> QuestionDetail:
    q = session.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")

    p = session.get(QuestionProgress, question_id)
    if p is None:
        p = QuestionProgress(question_id=question_id)
        session.add(p)

    if body.status is not None:
        p.status = body.status
    if body.score is not None:
        p.score = body.score
    if body.notes is not None:
        p.notes = body.notes
    p.last_practiced_at = datetime.utcnow()
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)

    return get_question(question_id, session)


@router.post("/admin/reimport")
def reimport(body: ImportRequest, session: Session = Depends(get_session)) -> dict:
    repo_root = default_repo_root()
    if body.path:
        target = Path(body.path)
        if not target.is_absolute():
            target = repo_root / target
    else:
        target = repo_root / "综合版" / "03_题库与答案"

    report = import_paths(session, [target], repo_root=repo_root, force=body.force)
    return report.as_dict()
