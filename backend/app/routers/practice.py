"""Practice APIs: Feynman drafts + Simon goal trees."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    FeynmanDraft,
    FeynmanStatus,
    Question,
    QuestionProgress,
    QuestionStatus,
    SimonGoal,
    SimonNode,
    SimonNodeProgress,
    SimonNodeStatus,
)
from app.simon_seed import ensure_simon_seeded, seed_simon_trees

router = APIRouter(tags=["practice"])


# ---- Feynman ----


class FeynmanChecklist(BaseModel):
    conclusion: bool = False
    mechanism: bool = False
    example: bool = False
    tradeoff: bool = False
    metric: bool = False
    followup: bool = False


class FeynmanDraftOut(BaseModel):
    id: int
    question_id: str
    question_title: str = ""
    conclusion: str
    mechanism: str
    example: str
    tradeoff: str
    metric: str
    checklist: FeynmanChecklist
    status: FeynmanStatus
    mark_recited: bool
    # Only populated after submit/compare
    reference_answer_md: Optional[str] = None
    reference_followups_md: Optional[str] = None
    reference_tradeoffs_md: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FeynmanUpsert(BaseModel):
    question_id: str
    conclusion: str = ""
    mechanism: str = ""
    example: str = ""
    tradeoff: str = ""
    metric: str = ""
    checklist: Optional[FeynmanChecklist] = None


class FeynmanSubmit(BaseModel):
    mark_recited: bool = False
    checklist: Optional[FeynmanChecklist] = None


def _checklist_loads(raw: str) -> FeynmanChecklist:
    try:
        data = json.loads(raw or "{}")
        return FeynmanChecklist(**data) if isinstance(data, dict) else FeynmanChecklist()
    except (json.JSONDecodeError, TypeError, ValueError):
        return FeynmanChecklist()


def _to_feynman_out(
    row: FeynmanDraft,
    question: Question | None,
    *,
    include_reference: bool,
) -> FeynmanDraftOut:
    assert row.id is not None
    show_ref = include_reference or row.status in (
        FeynmanStatus.submitted,
        FeynmanStatus.compared,
    )
    return FeynmanDraftOut(
        id=row.id,
        question_id=row.question_id,
        question_title=question.title if question else "",
        conclusion=row.conclusion,
        mechanism=row.mechanism,
        example=row.example,
        tradeoff=row.tradeoff,
        metric=row.metric,
        checklist=_checklist_loads(row.checklist_json),
        status=row.status,
        mark_recited=row.mark_recited,
        reference_answer_md=question.answer_md if show_ref and question else None,
        reference_followups_md=question.followups_md if show_ref and question else None,
        reference_tradeoffs_md=question.tradeoffs_md if show_ref and question else None,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/practice/feynman", response_model=list[FeynmanDraftOut])
def list_feynman(session: Session = Depends(get_session)) -> list[FeynmanDraftOut]:
    rows = session.exec(select(FeynmanDraft).order_by(FeynmanDraft.updated_at.desc())).all()
    out = []
    for row in rows:
        q = session.get(Question, row.question_id)
        out.append(_to_feynman_out(row, q, include_reference=False))
    return out


@router.get("/practice/feynman/by-question/{question_id}", response_model=FeynmanDraftOut | None)
def get_feynman_by_question(
    question_id: str,
    session: Session = Depends(get_session),
) -> FeynmanDraftOut | None:
    row = session.exec(
        select(FeynmanDraft)
        .where(FeynmanDraft.question_id == question_id)
        .order_by(FeynmanDraft.updated_at.desc())
    ).first()
    if row is None:
        return None
    q = session.get(Question, question_id)
    return _to_feynman_out(row, q, include_reference=False)


@router.post("/practice/feynman", response_model=FeynmanDraftOut)
def upsert_feynman_draft(
    body: FeynmanUpsert,
    session: Session = Depends(get_session),
) -> FeynmanDraftOut:
    q = session.get(Question, body.question_id)
    if q is None:
        raise HTTPException(404, "Question not found")

    row = session.exec(
        select(FeynmanDraft)
        .where(FeynmanDraft.question_id == body.question_id)
        .where(FeynmanDraft.status == FeynmanStatus.drafting)
        .order_by(FeynmanDraft.updated_at.desc())
    ).first()
    if row is None:
        row = FeynmanDraft(question_id=body.question_id)

    row.conclusion = body.conclusion
    row.mechanism = body.mechanism
    row.example = body.example
    row.tradeoff = body.tradeoff
    row.metric = body.metric
    if body.checklist is not None:
        row.checklist_json = body.checklist.model_dump_json()
    row.status = FeynmanStatus.drafting
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_feynman_out(row, q, include_reference=False)


@router.post("/practice/feynman/{draft_id}/submit", response_model=FeynmanDraftOut)
def submit_feynman(
    draft_id: int,
    body: FeynmanSubmit,
    session: Session = Depends(get_session),
) -> FeynmanDraftOut:
    row = session.get(FeynmanDraft, draft_id)
    if row is None:
        raise HTTPException(404, "Draft not found")
    q = session.get(Question, row.question_id)
    if q is None:
        raise HTTPException(404, "Question not found")

    # Require minimal structure before revealing
    filled = sum(
        1
        for part in (row.conclusion, row.mechanism, row.example, row.tradeoff, row.metric)
        if part.strip()
    )
    if filled < 3:
        raise HTTPException(400, "请至少填写五层中的 3 项后再提交对照")

    if body.checklist is not None:
        row.checklist_json = body.checklist.model_dump_json()
    row.status = FeynmanStatus.compared
    row.mark_recited = body.mark_recited
    row.updated_at = datetime.utcnow()
    session.add(row)

    if body.mark_recited:
        progress = session.get(QuestionProgress, row.question_id)
        if progress is None:
            progress = QuestionProgress(question_id=row.question_id)
        progress.status = QuestionStatus.recited
        progress.last_practiced_at = datetime.utcnow()
        progress.updated_at = datetime.utcnow()
        session.add(progress)

    session.commit()
    session.refresh(row)
    return _to_feynman_out(row, q, include_reference=True)


@router.post("/practice/feynman/{draft_id}/reset", response_model=FeynmanDraftOut)
def reset_feynman(draft_id: int, session: Session = Depends(get_session)) -> FeynmanDraftOut:
    old = session.get(FeynmanDraft, draft_id)
    if old is None:
        raise HTTPException(404, "Draft not found")
    q = session.get(Question, old.question_id)
    row = FeynmanDraft(question_id=old.question_id, status=FeynmanStatus.drafting)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_feynman_out(row, q, include_reference=False)


# ---- Simon ----


class SimonNodeOut(BaseModel):
    id: str
    goal_id: str
    title: str
    description: str
    linked_question_ids: list[str]
    linked_whiteboard_ids: list[str]
    sort_order: int
    status: SimonNodeStatus
    self_score: Optional[int] = None
    blocker_note: str = ""


class SimonGoalOut(BaseModel):
    id: str
    title: str
    description: str
    sort_order: int
    nodes: list[SimonNodeOut]
    passed_count: int
    total_count: int


class SimonNodeUpdate(BaseModel):
    status: Optional[SimonNodeStatus] = None
    self_score: Optional[int] = Field(default=None, ge=1, le=5)
    blocker_note: Optional[str] = None


def _split_ids(raw: str) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


@router.get("/practice/simon", response_model=list[SimonGoalOut])
def list_simon(session: Session = Depends(get_session)) -> list[SimonGoalOut]:
    ensure_simon_seeded(session)
    goals = session.exec(select(SimonGoal).order_by(SimonGoal.sort_order)).all()
    nodes = session.exec(select(SimonNode)).all()
    progress = {p.node_id: p for p in session.exec(select(SimonNodeProgress)).all()}
    by_goal: dict[str, list[SimonNode]] = {}
    for n in nodes:
        by_goal.setdefault(n.goal_id, []).append(n)

    out: list[SimonGoalOut] = []
    for g in goals:
        goal_nodes = sorted(by_goal.get(g.id, []), key=lambda x: x.sort_order)
        node_outs: list[SimonNodeOut] = []
        passed = 0
        for n in goal_nodes:
            p = progress.get(n.id)
            status = p.status if p else SimonNodeStatus.todo
            if status == SimonNodeStatus.passed:
                passed += 1
            node_outs.append(
                SimonNodeOut(
                    id=n.id,
                    goal_id=n.goal_id,
                    title=n.title,
                    description=n.description,
                    linked_question_ids=_split_ids(n.linked_question_ids),
                    linked_whiteboard_ids=_split_ids(n.linked_whiteboard_ids),
                    sort_order=n.sort_order,
                    status=status,
                    self_score=p.self_score if p else None,
                    blocker_note=p.blocker_note if p else "",
                )
            )
        out.append(
            SimonGoalOut(
                id=g.id,
                title=g.title,
                description=g.description,
                sort_order=g.sort_order,
                nodes=node_outs,
                passed_count=passed,
                total_count=len(node_outs),
            )
        )
    return out


@router.patch("/practice/simon/nodes/{node_id}", response_model=SimonNodeOut)
def patch_simon_node(
    node_id: str,
    body: SimonNodeUpdate,
    session: Session = Depends(get_session),
) -> SimonNodeOut:
    node = session.get(SimonNode, node_id)
    if node is None:
        raise HTTPException(404, "Node not found")
    p = session.get(SimonNodeProgress, node_id)
    if p is None:
        p = SimonNodeProgress(node_id=node_id)
    if body.status is not None:
        p.status = body.status
    if body.self_score is not None:
        p.self_score = body.self_score
        if body.self_score >= 4 and p.status != SimonNodeStatus.passed:
            p.status = SimonNodeStatus.passed
        elif body.self_score <= 2:
            p.status = SimonNodeStatus.stuck
        elif p.status == SimonNodeStatus.todo:
            p.status = SimonNodeStatus.practicing
    if body.blocker_note is not None:
        p.blocker_note = body.blocker_note
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return SimonNodeOut(
        id=node.id,
        goal_id=node.goal_id,
        title=node.title,
        description=node.description,
        linked_question_ids=_split_ids(node.linked_question_ids),
        linked_whiteboard_ids=_split_ids(node.linked_whiteboard_ids),
        sort_order=node.sort_order,
        status=p.status,
        self_score=p.self_score,
        blocker_note=p.blocker_note,
    )


@router.post("/practice/simon/reseed")
def reseed_simon(session: Session = Depends(get_session)) -> dict:
    n = seed_simon_trees(session)
    return {"nodes": n}
