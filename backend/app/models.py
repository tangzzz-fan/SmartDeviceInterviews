from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class QuestionStatus(str, Enum):
    todo = "todo"
    reviewed = "reviewed"
    recited = "recited"


class PracticeStatus(str, Enum):
    todo = "todo"
    practiced = "practiced"
    mastered = "mastered"


class SkillLevel(str, Enum):
    continuous = "能连续讲"
    skeleton = "能讲骨架"
    concept = "只能背概念"
    never = "没做过"


class SnapshotKey(str, Enum):
    d1 = "d1"
    d7 = "d7"


class ContentSource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    content_hash: str
    last_imported_at: datetime = Field(default_factory=datetime.utcnow)
    entity_type: str = "question"


class Question(SQLModel, table=True):
    id: str = Field(primary_key=True)
    module: str = Field(index=True)
    priority: str = Field(default="P0", index=True)
    title: str
    answer_md: str = ""
    followups_md: str = ""
    tradeoffs_md: str = ""
    source_path: str = ""
    orphaned: bool = Field(default=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionProgress(SQLModel, table=True):
    question_id: str = Field(primary_key=True, foreign_key="question.id")
    status: QuestionStatus = Field(default=QuestionStatus.todo)
    score: Optional[int] = Field(default=None, ge=1, le=5)
    notes: str = ""
    last_practiced_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChecklistItem(SQLModel, table=True):
    id: str = Field(primary_key=True)  # checklist:D1:1
    day_key: str = Field(index=True)  # D1 / D2 / pre24h
    day_title: str = ""
    sort_order: int = 0
    text: str
    source_path: str = ""
    orphaned: bool = False


class ChecklistProgress(SQLModel, table=True):
    item_id: str = Field(primary_key=True, foreign_key="checklistitem.id")
    checked: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DailyReflection(SQLModel, table=True):
    day_key: str = Field(primary_key=True)  # D1..D7
    findings: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Whiteboard(SQLModel, table=True):
    id: str = Field(primary_key=True)  # WB1
    title: str
    priority: str = "P0"
    body_md: str = ""
    source_path: str = ""
    orphaned: bool = False


class WhiteboardProgress(SQLModel, table=True):
    whiteboard_id: str = Field(primary_key=True, foreign_key="whiteboard.id")
    status: PracticeStatus = Field(default=PracticeStatus.todo)
    practiced_count: int = 0
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StarStory(SQLModel, table=True):
    id: str = Field(primary_key=True)  # S1
    title: str
    is_flagship: bool = False
    body_md: str = ""
    source_path: str = ""
    orphaned: bool = False


class StarProgress(SQLModel, table=True):
    story_id: str = Field(primary_key=True, foreign_key="starstory.id")
    filled_real_numbers: bool = False
    recited: bool = False
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EnglishScript(SQLModel, table=True):
    id: str = Field(primary_key=True)  # eng:intro-90
    title: str
    body_md: str = ""
    sort_order: int = 0
    source_path: str = ""
    orphaned: bool = False


class EnglishProgress(SQLModel, table=True):
    script_id: str = Field(primary_key=True, foreign_key="englishscript.id")
    practiced: bool = False
    recording_note: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SkillDimension(SQLModel, table=True):
    id: str = Field(primary_key=True)  # skill:swift-concurrency
    name: str
    prompt: str = ""
    criterion: str = ""
    group_name: str = "core"  # core | bonus
    sort_order: int = 0
    source_path: str = ""
    orphaned: bool = False


class SkillAssessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dimension_id: str = Field(foreign_key="skilldimension.id", index=True)
    snapshot: SnapshotKey = Field(index=True)
    level: Optional[SkillLevel] = None
    gap: str = ""  # 高/中/低
    evidence: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MockSession(SQLModel, table=True):
    """One mock interview run with per-item 1–5 scores."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = ""
    round_key: str = Field(index=True)  # R1 | R2 | custom
    scores_json: str = "[]"  # [{id,label,score}]
    average: Optional[float] = None
    passed: bool = False
    reflection: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FeynmanStatus(str, Enum):
    drafting = "drafting"
    submitted = "submitted"
    compared = "compared"


class FeynmanDraft(SQLModel, table=True):
    """Blind five-layer answer draft for a question (Feynman / teach-back)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: str = Field(index=True, foreign_key="question.id")
    conclusion: str = ""
    mechanism: str = ""
    example: str = ""
    tradeoff: str = ""
    metric: str = ""
    checklist_json: str = "{}"  # five-layer self-check bools
    status: FeynmanStatus = Field(default=FeynmanStatus.drafting)
    mark_recited: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SimonNodeStatus(str, Enum):
    todo = "todo"
    practicing = "practicing"
    passed = "passed"
    stuck = "stuck"


class SimonGoal(SQLModel, table=True):
    id: str = Field(primary_key=True)  # simon:ble-ready
    title: str
    description: str = ""
    sort_order: int = 0


class SimonNode(SQLModel, table=True):
    id: str = Field(primary_key=True)  # simon:ble-ready:ready-def
    goal_id: str = Field(index=True, foreign_key="simongoal.id")
    title: str
    description: str = ""
    linked_question_ids: str = ""  # comma-separated A1,B2
    linked_whiteboard_ids: str = ""
    sort_order: int = 0


class SimonNodeProgress(SQLModel, table=True):
    node_id: str = Field(primary_key=True, foreign_key="simonnode.id")
    status: SimonNodeStatus = Field(default=SimonNodeStatus.todo)
    self_score: Optional[int] = Field(default=None, ge=1, le=5)
    blocker_note: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ColumnDoc(SQLModel, table=True):
    """Markdown docs under 专栏_* (e.g. SmartGlass), separate from question bank."""

    id: str = Field(primary_key=True)  # glass:01_项目复盘
    column_key: str = Field(index=True)  # smartglass
    title: str
    filename: str
    body_md: str = ""
    sort_order: int = 0
    source_path: str = ""
    orphaned: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)
