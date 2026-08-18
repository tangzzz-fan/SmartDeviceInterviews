from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import MockSession, Question, QuestionProgress, QuestionStatus
from app.schemas_dashboard import DashboardResponse, LatestMock, ModuleStat, WeakQuestion

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(session: Session = Depends(get_session)) -> DashboardResponse:
    questions = session.exec(select(Question).where(Question.orphaned == False)).all()  # noqa: E712
    progress_rows = session.exec(select(QuestionProgress)).all()
    progress = {p.question_id: p for p in progress_rows}

    total = len(questions)
    todo = reviewed = recited = 0
    by_module: dict[str, dict[str, int]] = {}
    weak: list[WeakQuestion] = []

    for q in questions:
        p = progress.get(q.id)
        status = p.status if p else QuestionStatus.todo
        score = p.score if p else None

        if status == QuestionStatus.todo:
            todo += 1
        elif status == QuestionStatus.reviewed:
            reviewed += 1
        else:
            recited += 1

        bucket = by_module.setdefault(
            q.module,
            {"total": 0, "todo": 0, "reviewed": 0, "recited": 0, "weak": 0},
        )
        bucket["total"] += 1
        bucket[status.value] += 1

        if score is not None and score <= 2:
            bucket["weak"] += 1
            weak.append(
                WeakQuestion(
                    id=q.id,
                    title=q.title,
                    module=q.module,
                    status=status,
                    score=score,
                )
            )

    if len(weak) < 8:
        for q in questions:
            if len(weak) >= 8:
                break
            if any(w.id == q.id for w in weak):
                continue
            p = progress.get(q.id)
            status = p.status if p else QuestionStatus.todo
            if status != QuestionStatus.recited:
                weak.append(
                    WeakQuestion(
                        id=q.id,
                        title=q.title,
                        module=q.module,
                        status=status,
                        score=p.score if p else None,
                    )
                )

    modules = [
        ModuleStat(
            module=name,
            total=stats["total"],
            todo=stats["todo"],
            reviewed=stats["reviewed"],
            recited=stats["recited"],
            weak=stats["weak"],
        )
        for name, stats in sorted(by_module.items())
    ]

    latest_row = session.exec(
        select(MockSession).order_by(MockSession.created_at.desc())
    ).first()
    latest_mock = None
    if latest_row and latest_row.id is not None:
        latest_mock = LatestMock(
            id=latest_row.id,
            title=latest_row.title,
            round_key=latest_row.round_key,
            average=latest_row.average,
            passed=latest_row.passed,
        )

    return DashboardResponse(
        total=total,
        todo=todo,
        reviewed=reviewed,
        recited=recited,
        modules=modules,
        weak_questions=weak[:10],
        latest_mock=latest_mock,
    )
