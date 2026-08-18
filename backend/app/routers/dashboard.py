from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    MockSession,
    Question,
    QuestionProgress,
    QuestionStatus,
    SimonGoal,
    SimonNode,
    SimonNodeProgress,
    SimonNodeStatus,
)
from app.schemas_dashboard import (
    DashboardResponse,
    LatestMock,
    ModuleStat,
    OpenSimonNode,
    WeakQuestion,
)
from app.simon_seed import ensure_simon_seeded

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

    open_simon: list[OpenSimonNode] = []
    try:
        ensure_simon_seeded(session)
        goals = {g.id: g for g in session.exec(select(SimonGoal)).all()}
        nodes = session.exec(select(SimonNode)).all()
        node_progress = {p.node_id: p for p in session.exec(select(SimonNodeProgress)).all()}
        for n in sorted(nodes, key=lambda x: (x.goal_id, x.sort_order)):
            p = node_progress.get(n.id)
            status = p.status if p else SimonNodeStatus.todo
            if status != SimonNodeStatus.passed:
                goal = goals.get(n.goal_id)
                open_simon.append(
                    OpenSimonNode(
                        id=n.id,
                        goal_title=goal.title if goal else n.goal_id,
                        title=n.title,
                        status=status.value,
                    )
                )
            if len(open_simon) >= 6:
                break
    except Exception:  # noqa: BLE001 — dashboard should still work pre-migration
        open_simon = []

    return DashboardResponse(
        total=total,
        todo=todo,
        reviewed=reviewed,
        recited=recited,
        modules=modules,
        weak_questions=weak[:10],
        latest_mock=latest_mock,
        open_simon_nodes=open_simon,
    )
