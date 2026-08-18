from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.mocking import (
    MOCK_TEMPLATES,
    compute_result,
    dumps_scores,
    loads_scores,
    template_items,
)
from app.models import MockSession

router = APIRouter(tags=["mocks"])


class ScoreItem(BaseModel):
    id: str
    label: str
    score: Optional[int] = Field(default=None, ge=1, le=5)


class MockSessionOut(BaseModel):
    id: int
    title: str
    round_key: str
    scores: list[ScoreItem]
    average: Optional[float] = None
    passed: bool
    reflection: str
    created_at: datetime
    updated_at: datetime


class MockCreate(BaseModel):
    round_key: str = "R1"
    title: Optional[str] = None


class MockUpdate(BaseModel):
    title: Optional[str] = None
    scores: Optional[list[ScoreItem]] = None
    reflection: Optional[str] = None


def _to_out(row: MockSession) -> MockSessionOut:
    scores = [ScoreItem(**s) for s in loads_scores(row.scores_json)]
    assert row.id is not None
    return MockSessionOut(
        id=row.id,
        title=row.title,
        round_key=row.round_key,
        scores=scores,
        average=row.average,
        passed=row.passed,
        reflection=row.reflection,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/mocks/templates")
def list_templates() -> dict[str, list[dict[str, str]]]:
    return MOCK_TEMPLATES


@router.get("/mocks", response_model=list[MockSessionOut])
def list_mocks(session: Session = Depends(get_session)) -> list[MockSessionOut]:
    rows = session.exec(select(MockSession).order_by(MockSession.created_at.desc())).all()
    return [_to_out(r) for r in rows]


@router.post("/mocks", response_model=MockSessionOut)
def create_mock(body: MockCreate, session: Session = Depends(get_session)) -> MockSessionOut:
    if body.round_key not in MOCK_TEMPLATES:
        raise HTTPException(400, f"Unknown round_key. Choose from: {list(MOCK_TEMPLATES)}")
    title = body.title or f"模拟面 {body.round_key}"
    scores = template_items(body.round_key)
    row = MockSession(
        title=title,
        round_key=body.round_key,
        scores_json=dumps_scores(scores),
        average=None,
        passed=False,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_out(row)


@router.get("/mocks/{mock_id}", response_model=MockSessionOut)
def get_mock(mock_id: int, session: Session = Depends(get_session)) -> MockSessionOut:
    row = session.get(MockSession, mock_id)
    if row is None:
        raise HTTPException(404, "Mock session not found")
    return _to_out(row)


@router.patch("/mocks/{mock_id}", response_model=MockSessionOut)
def update_mock(
    mock_id: int,
    body: MockUpdate,
    session: Session = Depends(get_session),
) -> MockSessionOut:
    row = session.get(MockSession, mock_id)
    if row is None:
        raise HTTPException(404, "Mock session not found")
    if body.title is not None:
        row.title = body.title
    if body.reflection is not None:
        row.reflection = body.reflection
    if body.scores is not None:
        scores: list[dict[str, Any]] = [s.model_dump() for s in body.scores]
        average, passed = compute_result(scores)
        row.scores_json = dumps_scores(scores)
        row.average = average
        row.passed = passed
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_out(row)


@router.delete("/mocks/{mock_id}")
def delete_mock(mock_id: int, session: Session = Depends(get_session)) -> dict:
    row = session.get(MockSession, mock_id)
    if row is None:
        raise HTTPException(404, "Mock session not found")
    session.delete(row)
    session.commit()
    return {"ok": True}
