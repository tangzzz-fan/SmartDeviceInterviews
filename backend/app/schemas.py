from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import QuestionStatus


class QuestionListItem(BaseModel):
    id: str
    module: str
    priority: str
    title: str
    status: QuestionStatus
    score: Optional[int] = None
    last_practiced_at: Optional[datetime] = None
    orphaned: bool = False


class QuestionDetail(BaseModel):
    id: str
    module: str
    priority: str
    title: str
    answer_md: str
    followups_md: str
    tradeoffs_md: str
    source_path: str
    orphaned: bool
    status: QuestionStatus
    score: Optional[int] = None
    notes: str = ""
    last_practiced_at: Optional[datetime] = None


class QuestionProgressUpdate(BaseModel):
    status: Optional[QuestionStatus] = None
    score: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = None


class ImportRequest(BaseModel):
    path: Optional[str] = None
    force: bool = False
