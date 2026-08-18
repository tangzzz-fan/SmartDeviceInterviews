"""Parse interview question markdown into structured records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

QUESTION_HEADING = re.compile(
    r"^##\s+(?P<id>[A-Z]+\d+)\.\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)

# Match **Label**： either alone or with same-line content
SECTION_SPLIT = re.compile(
    r"^\*\*(?P<label>[^*]+)\*\*[：:]\s*(?P<inline>.*)$",
    re.MULTILINE,
)

ANSWER_LABELS = {
    "答案",
    "要点",
    "示范骨架",
    "骨架",
    "答案（疑难 bug 模板）",
    "答案（连接抢占）",
    "答案（系统验证）",
    "答案（连不上漏斗）",
}

FOLLOWUP_LABELS = {"追问应对", "追问点", "反问清单"}

TRADEOFF_LABELS = {
    "取舍",
    "边界",
    "诚实补充",
    "边界必须坦白",
    "成熟度信号",
    "判断标准",
    "为什么是我",
    "拒绝「快」的场景",
    "代价",
    "预期产出",
    "试过后放弃的",
    "案例",
    "翻车案例（必备反例）",
    "效果指标",
    "安全红线第一天就定",
}

MODULE_FROM_STEM = re.compile(r"^\d+-(.+)$")


@dataclass
class ParsedQuestion:
    id: str
    title: str
    module: str
    priority: str
    answer_md: str
    followups_md: str
    tradeoffs_md: str
    source_path: str


def infer_module(path: Path) -> str:
    match = MODULE_FROM_STEM.match(path.stem)
    return match.group(1) if match else path.stem


def infer_priority(text: str) -> str:
    head = text[:500]
    if re.search(r"[（(]P1[）)]", head):
        return "P1"
    if re.search(r"[（(]P0[）)]|\bP0\b", head):
        return "P0"
    return "P0"


def _bucket_for_label(label: str) -> str:
    cleaned = label.strip()
    if cleaned in ANSWER_LABELS or cleaned.startswith("答案"):
        return "answer_md"
    if cleaned in FOLLOWUP_LABELS or cleaned.startswith("追问"):
        return "followups_md"
    if cleaned in TRADEOFF_LABELS or cleaned.startswith("边界") or cleaned.startswith("取舍"):
        return "tradeoffs_md"
    # Unknown labeled blocks still go into the answer so nothing is lost
    return "answer_md"


def _split_sections(body: str) -> dict[str, str]:
    parts: dict[str, list[str]] = {
        "answer_md": [],
        "followups_md": [],
        "tradeoffs_md": [],
    }
    matches = list(SECTION_SPLIT.finditer(body))
    if not matches:
        text = body.strip()
        if text:
            parts["answer_md"].append(text)
        return {k: "\n\n".join(v).strip() for k, v in parts.items()}

    preamble = body[: matches[0].start()].strip()
    if preamble:
        parts["answer_md"].append(preamble)

    for i, match in enumerate(matches):
        label = match.group("label").strip()
        bucket = _bucket_for_label(label)
        inline = match.group("inline").strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        rest = body[start:end].strip()
        chunks: list[str] = []
        if inline:
            chunks.append(inline)
        if rest:
            chunks.append(rest)
        block = "\n\n".join(chunks).strip()
        if not block:
            continue
        # Keep label context for non-canonical answer sections
        if label not in {"答案", "追问应对", "取舍"}:
            block = f"**{label}**：\n\n{block}"
        parts[bucket].append(block)

    return {k: "\n\n".join(v).strip() for k, v in parts.items()}


def parse_questions_markdown(path: Path, *, repo_relative: str | None = None) -> list[ParsedQuestion]:
    text = path.read_text(encoding="utf-8")
    module = infer_module(path)
    priority = infer_priority(text)
    source = repo_relative or str(path)

    headings = list(QUESTION_HEADING.finditer(text))
    results: list[ParsedQuestion] = []

    for i, match in enumerate(headings):
        qid = match.group("id")
        title = match.group("title").strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end].strip()
        # Stop at horizontal rules that separate major sections inside a file
        if "\n---\n" in body:
            body = body.split("\n---\n", 1)[0].strip()
        sections = _split_sections(body)
        results.append(
            ParsedQuestion(
                id=qid,
                title=title,
                module=module,
                priority=priority,
                answer_md=sections["answer_md"],
                followups_md=sections["followups_md"],
                tradeoffs_md=sections["tradeoffs_md"],
                source_path=source,
            )
        )
    return results
