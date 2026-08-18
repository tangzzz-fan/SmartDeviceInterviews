from pydantic import BaseModel

from app.models import QuestionStatus


class ModuleStat(BaseModel):
    module: str
    total: int
    todo: int
    reviewed: int
    recited: int
    weak: int


class WeakQuestion(BaseModel):
    id: str
    title: str
    module: str
    status: QuestionStatus
    score: int | None = None


class LatestMock(BaseModel):
    id: int
    title: str
    round_key: str
    average: float | None = None
    passed: bool


class OpenSimonNode(BaseModel):
    id: str
    goal_title: str
    title: str
    status: str


class DashboardResponse(BaseModel):
    total: int
    todo: int
    reviewed: int
    recited: int
    modules: list[ModuleStat]
    weak_questions: list[WeakQuestion]
    latest_mock: LatestMock | None = None
    open_simon_nodes: list[OpenSimonNode] = []
