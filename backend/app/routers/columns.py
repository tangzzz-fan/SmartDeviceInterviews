from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import ColumnDoc

router = APIRouter(tags=["columns"])


class ColumnDocListItem(BaseModel):
    id: str
    column_key: str
    title: str
    filename: str
    sort_order: int


class ColumnDocDetail(ColumnDocListItem):
    body_md: str
    source_path: str


@router.get("/columns/{column_key}", response_model=list[ColumnDocListItem])
def list_column_docs(
    column_key: str,
    session: Session = Depends(get_session),
) -> list[ColumnDocListItem]:
    rows = session.exec(
        select(ColumnDoc)
        .where(ColumnDoc.column_key == column_key)
        .where(ColumnDoc.orphaned == False)  # noqa: E712
        .order_by(ColumnDoc.sort_order)
    ).all()
    return [
        ColumnDocListItem(
            id=r.id,
            column_key=r.column_key,
            title=r.title,
            filename=r.filename,
            sort_order=r.sort_order,
        )
        for r in rows
    ]


@router.get("/columns/{column_key}/docs/{doc_id:path}", response_model=ColumnDocDetail)
def get_column_doc(
    column_key: str,
    doc_id: str,
    session: Session = Depends(get_session),
) -> ColumnDocDetail:
    # Accept full id or bare stem
    full_id = doc_id if ":" in doc_id else f"{column_key}:{doc_id}"
    row = session.get(ColumnDoc, full_id)
    if row is None or row.column_key != column_key:
        raise HTTPException(404, "Document not found")
    return ColumnDocDetail(
        id=row.id,
        column_key=row.column_key,
        title=row.title,
        filename=row.filename,
        sort_order=row.sort_order,
        body_md=row.body_md,
        source_path=row.source_path,
    )
