from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models import (
    ChecklistItem,
    ChecklistProgress,
    DailyReflection,
    EnglishProgress,
    EnglishScript,
    PracticeStatus,
    SkillAssessment,
    SkillDimension,
    SkillLevel,
    SnapshotKey,
    StarProgress,
    StarStory,
    Whiteboard,
    WhiteboardProgress,
)

router = APIRouter(tags=["tracker"])


# ---- Checklist ----


class ChecklistItemOut(BaseModel):
    id: str
    day_key: str
    day_title: str
    sort_order: int
    text: str
    checked: bool


class ChecklistDayOut(BaseModel):
    day_key: str
    day_title: str
    items: list[ChecklistItemOut]
    reflection: str = ""


class ChecklistCheckUpdate(BaseModel):
    checked: bool


class ReflectionUpdate(BaseModel):
    findings: str


@router.get("/checklist", response_model=list[ChecklistDayOut])
def get_checklist(session: Session = Depends(get_session)) -> list[ChecklistDayOut]:
    items = session.exec(
        select(ChecklistItem).where(ChecklistItem.orphaned == False)  # noqa: E712
    ).all()
    progress = {
        p.item_id: p
        for p in session.exec(select(ChecklistProgress)).all()
    }
    reflections = {
        r.day_key: r.findings
        for r in session.exec(select(DailyReflection)).all()
    }

    days: dict[str, ChecklistDayOut] = {}
    order_keys = [f"D{i}" for i in range(1, 8)] + ["pre24h"]
    for item in sorted(items, key=lambda x: (order_keys.index(x.day_key) if x.day_key in order_keys else 99, x.sort_order)):
        day = days.get(item.day_key)
        if day is None:
            day = ChecklistDayOut(
                day_key=item.day_key,
                day_title=item.day_title,
                items=[],
                reflection=reflections.get(item.day_key, ""),
            )
            days[item.day_key] = day
        p = progress.get(item.id)
        day.items.append(
            ChecklistItemOut(
                id=item.id,
                day_key=item.day_key,
                day_title=item.day_title,
                sort_order=item.sort_order,
                text=item.text,
                checked=bool(p.checked) if p else False,
            )
        )
    return [days[k] for k in order_keys if k in days]


@router.patch("/checklist/{item_id}", response_model=ChecklistItemOut)
def patch_checklist(
    item_id: str,
    body: ChecklistCheckUpdate,
    session: Session = Depends(get_session),
) -> ChecklistItemOut:
    item = session.get(ChecklistItem, item_id)
    if item is None:
        raise HTTPException(404, "Checklist item not found")
    p = session.get(ChecklistProgress, item_id)
    if p is None:
        p = ChecklistProgress(item_id=item_id)
    p.checked = body.checked
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    return ChecklistItemOut(
        id=item.id,
        day_key=item.day_key,
        day_title=item.day_title,
        sort_order=item.sort_order,
        text=item.text,
        checked=p.checked,
    )


@router.put("/reflections/{day_key}")
def put_reflection(
    day_key: str,
    body: ReflectionUpdate,
    session: Session = Depends(get_session),
) -> dict:
    row = session.get(DailyReflection, day_key)
    if row is None:
        row = DailyReflection(day_key=day_key)
    row.findings = body.findings
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    return {"day_key": day_key, "findings": row.findings}


# ---- Whiteboards ----


class WhiteboardOut(BaseModel):
    id: str
    title: str
    priority: str
    body_md: str
    status: PracticeStatus
    practiced_count: int
    notes: str = ""


class WhiteboardUpdate(BaseModel):
    status: Optional[PracticeStatus] = None
    practiced_count: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    increment: bool = False


@router.get("/whiteboards", response_model=list[WhiteboardOut])
def list_whiteboards(session: Session = Depends(get_session)) -> list[WhiteboardOut]:
    rows = session.exec(select(Whiteboard).where(Whiteboard.orphaned == False)).all()  # noqa: E712
    rows = sorted(rows, key=lambda w: int(w.id.replace("WB", "") or 0))
    progress = {p.whiteboard_id: p for p in session.exec(select(WhiteboardProgress)).all()}
    out = []
    for w in rows:
        p = progress.get(w.id)
        out.append(
            WhiteboardOut(
                id=w.id,
                title=w.title,
                priority=w.priority,
                body_md=w.body_md,
                status=p.status if p else PracticeStatus.todo,
                practiced_count=p.practiced_count if p else 0,
                notes=p.notes if p else "",
            )
        )
    return out


@router.patch("/whiteboards/{wb_id}", response_model=WhiteboardOut)
def patch_whiteboard(
    wb_id: str,
    body: WhiteboardUpdate,
    session: Session = Depends(get_session),
) -> WhiteboardOut:
    w = session.get(Whiteboard, wb_id)
    if w is None:
        raise HTTPException(404, "Whiteboard not found")
    p = session.get(WhiteboardProgress, wb_id)
    if p is None:
        p = WhiteboardProgress(whiteboard_id=wb_id)
    if body.increment:
        p.practiced_count += 1
        if p.status == PracticeStatus.todo:
            p.status = PracticeStatus.practiced
    if body.status is not None:
        p.status = body.status
    if body.practiced_count is not None:
        p.practiced_count = body.practiced_count
    if body.notes is not None:
        p.notes = body.notes
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return WhiteboardOut(
        id=w.id,
        title=w.title,
        priority=w.priority,
        body_md=w.body_md,
        status=p.status,
        practiced_count=p.practiced_count,
        notes=p.notes,
    )


# ---- STAR ----


class StarOut(BaseModel):
    id: str
    title: str
    is_flagship: bool
    body_md: str
    filled_real_numbers: bool
    recited: bool
    notes: str = ""


class StarUpdate(BaseModel):
    filled_real_numbers: Optional[bool] = None
    recited: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/stories", response_model=list[StarOut])
def list_stories(session: Session = Depends(get_session)) -> list[StarOut]:
    rows = session.exec(select(StarStory).where(StarStory.orphaned == False)).all()  # noqa: E712
    rows = sorted(rows, key=lambda s: int(s.id.replace("S", "") or 0))
    progress = {p.story_id: p for p in session.exec(select(StarProgress)).all()}
    return [
        StarOut(
            id=s.id,
            title=s.title,
            is_flagship=s.is_flagship,
            body_md=s.body_md,
            filled_real_numbers=progress[s.id].filled_real_numbers if s.id in progress else False,
            recited=progress[s.id].recited if s.id in progress else False,
            notes=progress[s.id].notes if s.id in progress else "",
        )
        for s in rows
    ]


@router.patch("/stories/{story_id}", response_model=StarOut)
def patch_story(
    story_id: str,
    body: StarUpdate,
    session: Session = Depends(get_session),
) -> StarOut:
    s = session.get(StarStory, story_id)
    if s is None:
        raise HTTPException(404, "Story not found")
    p = session.get(StarProgress, story_id)
    if p is None:
        p = StarProgress(story_id=story_id)
    if body.filled_real_numbers is not None:
        p.filled_real_numbers = body.filled_real_numbers
    if body.recited is not None:
        p.recited = body.recited
    if body.notes is not None:
        p.notes = body.notes
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return StarOut(
        id=s.id,
        title=s.title,
        is_flagship=s.is_flagship,
        body_md=s.body_md,
        filled_real_numbers=p.filled_real_numbers,
        recited=p.recited,
        notes=p.notes,
    )


# ---- English ----


class EnglishOut(BaseModel):
    id: str
    title: str
    body_md: str
    practiced: bool
    recording_note: str = ""


class EnglishUpdate(BaseModel):
    practiced: Optional[bool] = None
    recording_note: Optional[str] = None


@router.get("/english", response_model=list[EnglishOut])
def list_english(session: Session = Depends(get_session)) -> list[EnglishOut]:
    rows = session.exec(select(EnglishScript).where(EnglishScript.orphaned == False)).all()  # noqa: E712
    rows = sorted(rows, key=lambda e: e.sort_order)
    progress = {p.script_id: p for p in session.exec(select(EnglishProgress)).all()}
    return [
        EnglishOut(
            id=e.id,
            title=e.title,
            body_md=e.body_md,
            practiced=progress[e.id].practiced if e.id in progress else False,
            recording_note=progress[e.id].recording_note if e.id in progress else "",
        )
        for e in rows
    ]


@router.patch("/english/{script_id}", response_model=EnglishOut)
def patch_english(
    script_id: str,
    body: EnglishUpdate,
    session: Session = Depends(get_session),
) -> EnglishOut:
    e = session.get(EnglishScript, script_id)
    if e is None:
        raise HTTPException(404, "Script not found")
    p = session.get(EnglishProgress, script_id)
    if p is None:
        p = EnglishProgress(script_id=script_id)
    if body.practiced is not None:
        p.practiced = body.practiced
    if body.recording_note is not None:
        p.recording_note = body.recording_note
    p.updated_at = datetime.utcnow()
    session.add(p)
    session.commit()
    session.refresh(p)
    return EnglishOut(
        id=e.id,
        title=e.title,
        body_md=e.body_md,
        practiced=p.practiced,
        recording_note=p.recording_note,
    )


# ---- Skills ----


class SkillDimOut(BaseModel):
    id: str
    name: str
    prompt: str
    criterion: str
    group_name: str
    d1_level: Optional[SkillLevel] = None
    d1_gap: str = ""
    d1_evidence: str = ""
    d7_level: Optional[SkillLevel] = None
    d7_gap: str = ""
    d7_evidence: str = ""


class SkillUpdate(BaseModel):
    snapshot: SnapshotKey
    level: Optional[SkillLevel] = None
    gap: Optional[str] = None
    evidence: Optional[str] = None


@router.get("/skills", response_model=list[SkillDimOut])
def list_skills(session: Session = Depends(get_session)) -> list[SkillDimOut]:
    dims = session.exec(
        select(SkillDimension).where(SkillDimension.orphaned == False)  # noqa: E712
    ).all()
    dims = sorted(dims, key=lambda d: (0 if d.group_name == "core" else 1, d.sort_order))
    assessments = session.exec(select(SkillAssessment)).all()
    by_key = {(a.dimension_id, a.snapshot): a for a in assessments}
    out: list[SkillDimOut] = []
    for d in dims:
        d1 = by_key.get((d.id, SnapshotKey.d1))
        d7 = by_key.get((d.id, SnapshotKey.d7))
        out.append(
            SkillDimOut(
                id=d.id,
                name=d.name,
                prompt=d.prompt,
                criterion=d.criterion,
                group_name=d.group_name,
                d1_level=d1.level if d1 else None,
                d1_gap=d1.gap if d1 else "",
                d1_evidence=d1.evidence if d1 else "",
                d7_level=d7.level if d7 else None,
                d7_gap=d7.gap if d7 else "",
                d7_evidence=d7.evidence if d7 else "",
            )
        )
    return out


@router.patch("/skills/{dim_id}", response_model=SkillDimOut)
def patch_skill(
    dim_id: str,
    body: SkillUpdate,
    session: Session = Depends(get_session),
) -> SkillDimOut:
    d = session.get(SkillDimension, dim_id)
    if d is None:
        raise HTTPException(404, "Skill dimension not found")
    row = session.exec(
        select(SkillAssessment).where(
            SkillAssessment.dimension_id == dim_id,
            SkillAssessment.snapshot == body.snapshot,
        )
    ).first()
    if row is None:
        row = SkillAssessment(dimension_id=dim_id, snapshot=body.snapshot)
    if body.level is not None:
        row.level = body.level
    if body.gap is not None:
        row.gap = body.gap
    if body.evidence is not None:
        row.evidence = body.evidence
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    return next(x for x in list_skills(session) if x.id == dim_id)
