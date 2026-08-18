"""Parsers for non-question markdown content."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DAY_HEADING = re.compile(r"^##\s+(D\d+)[：:]\s*(.+?)\s*$", re.MULTILINE)
PRE24_HEADING = re.compile(r"^##\s+面试前\s*24\s*小时清单\s*$", re.MULTILINE)
CHECKBOX = re.compile(r"^- \[[ xX]\]\s+(.+)$", re.MULTILINE)

WB_HEADING = re.compile(
    r"^##\s+白板\s+(?P<num>\d+)[：:]\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)

STAR_HEADING = re.compile(
    r"^##\s+(?:★\s*)?(?P<id>S\d+)\.\s*(?P<title>.+?)\s*$",
    re.MULTILINE,
)
STAR_PATCH = re.compile(
    r"^-\s+\*\*(?P<id>S\d+)\s+(?P<title>[^*]+)\*\*[：:]\s*(?P<body>.+)$",
    re.MULTILINE,
)

ENG_SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
ENG_SUB = re.compile(r"^###\s+(?P<title>.+?)\s*$", re.MULTILINE)

SKILL_ROW = re.compile(
    r"^\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<prompt>[^|]+?)\s*\|\s*(?P<criterion>[^|]+?)\s*\|\s*待填\s*\|\s*高/中/低\s*\|",
    re.MULTILINE,
)
SKILL_BONUS_ROW = re.compile(
    r"^\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<prompt>[^|]+?)\s*\|\s*待填\s*\|\s*高/中/低\s*\|",
    re.MULTILINE,
)


@dataclass
class ParsedChecklistItem:
    id: str
    day_key: str
    day_title: str
    sort_order: int
    text: str
    source_path: str


@dataclass
class ParsedWhiteboard:
    id: str
    title: str
    priority: str
    body_md: str
    source_path: str


@dataclass
class ParsedStar:
    id: str
    title: str
    is_flagship: bool
    body_md: str
    source_path: str


@dataclass
class ParsedEnglish:
    id: str
    title: str
    body_md: str
    sort_order: int
    source_path: str


@dataclass
class ParsedSkill:
    id: str
    name: str
    prompt: str
    criterion: str
    group_name: str
    sort_order: int
    source_path: str


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.strip(), flags=re.UNICODE)
    return cleaned.strip("-").lower()[:48] or "item"


def parse_checklist(path: Path, *, repo_relative: str) -> list[ParsedChecklistItem]:
    text = path.read_text(encoding="utf-8")
    items: list[ParsedChecklistItem] = []

    day_matches = list(DAY_HEADING.finditer(text))
    for i, match in enumerate(day_matches):
        day_key = match.group(1)
        day_title = match.group(2).strip()
        start = match.end()
        end = day_matches[i + 1].start() if i + 1 < len(day_matches) else len(text)
        # stop before pre24 if present later
        pre = PRE24_HEADING.search(text, start, end)
        if pre:
            end = pre.start()
        body = text[start:end]
        boxes = CHECKBOX.findall(body)
        for idx, raw in enumerate(boxes, start=1):
            items.append(
                ParsedChecklistItem(
                    id=f"checklist:{day_key}:{idx}",
                    day_key=day_key,
                    day_title=day_title,
                    sort_order=idx,
                    text=raw.strip(),
                    source_path=repo_relative,
                )
            )

    pre_match = PRE24_HEADING.search(text)
    if pre_match:
        start = pre_match.end()
        end_marker = text.find("## 复盘区", start)
        end = end_marker if end_marker != -1 else len(text)
        boxes = CHECKBOX.findall(text[start:end])
        for idx, raw in enumerate(boxes, start=1):
            items.append(
                ParsedChecklistItem(
                    id=f"checklist:pre24h:{idx}",
                    day_key="pre24h",
                    day_title="面试前 24 小时",
                    sort_order=idx,
                    text=raw.strip(),
                    source_path=repo_relative,
                )
            )
    return items


def parse_whiteboards(path: Path, *, repo_relative: str) -> list[ParsedWhiteboard]:
    text = path.read_text(encoding="utf-8")
    matches = list(WB_HEADING.finditer(text))
    results: list[ParsedWhiteboard] = []
    for i, match in enumerate(matches):
        num = int(match.group("num"))
        title = match.group("title").strip()
        # strip trailing priority hints from title for display, keep in priority field
        priority = "P0" if num <= 4 else "bonus"
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if "\n---\n" in text[start:end]:
            end = start + text[start:end].index("\n---\n")
        body = text[start:end].strip()
        results.append(
            ParsedWhiteboard(
                id=f"WB{num}",
                title=title,
                priority=priority,
                body_md=body,
                source_path=repo_relative,
            )
        )
    return results


def parse_star_stories(path: Path, *, repo_relative: str) -> list[ParsedStar]:
    text = path.read_text(encoding="utf-8")
    results: list[ParsedStar] = []
    matches = list(STAR_HEADING.finditer(text))
    for i, match in enumerate(matches):
        sid = match.group("id")
        title = match.group("title").strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        # stop before 加分项 short patches section if heading-style ends
        section = text[start:end]
        if "## 加分项" in section:
            section = section.split("## 加分项", 1)[0]
        flagship = sid == "S1" or "旗舰" in title
        results.append(
            ParsedStar(
                id=sid,
                title=title,
                is_flagship=flagship,
                body_md=section.strip(),
                source_path=repo_relative,
            )
        )

    for match in STAR_PATCH.finditer(text):
        sid = match.group("id")
        if any(r.id == sid for r in results):
            continue
        results.append(
            ParsedStar(
                id=sid,
                title=match.group("title").strip(),
                is_flagship=False,
                body_md=match.group("body").strip(),
                source_path=repo_relative,
            )
        )
    results.sort(key=lambda s: int(re.sub(r"\D", "", s.id) or 0))
    return results


def parse_english(path: Path, *, repo_relative: str) -> list[ParsedEnglish]:
    """Import practice-oriented subsections / block sections as scripts."""
    text = path.read_text(encoding="utf-8")
    results: list[ParsedEnglish] = []
    order = 0

    # Prefer ### subsections under major sections for granular practice items
    sub_matches = list(ENG_SUB.finditer(text))
    if sub_matches:
        for i, match in enumerate(sub_matches):
            title = match.group("title").strip()
            start = match.end()
            end = sub_matches[i + 1].start() if i + 1 < len(sub_matches) else len(text)
            # also stop at next ##
            next_h2 = ENG_SECTION.search(text, start, end)
            if next_h2:
                end = next_h2.start()
            body = text[start:end].strip()
            if len(body) < 40:
                continue
            order += 1
            results.append(
                ParsedEnglish(
                    id=f"eng:{_slug(title)}-{order}",
                    title=title,
                    body_md=body,
                    sort_order=order,
                    source_path=repo_relative,
                )
            )

    # Also import key ## sections that are themselves practice blocks (二、Why this role)
    for match in ENG_SECTION.finditer(text):
        title = match.group("title").strip()
        if title.startswith("Rehearsal") or title.startswith("八") or title.startswith("九"):
            # include 九 as one script for reverse questions
            pass
        start = match.end()
        next_match = ENG_SECTION.search(text, start)
        end = next_match.start() if next_match else len(text)
        body = text[start:end].strip()
        # skip if already covered mostly by ### children
        if title.startswith("一、") or title.startswith("三、") or title.startswith("四、"):
            continue
        if len(body) < 80:
            continue
        # avoid duplicating if this section only contains ### we already parsed
        if ENG_SUB.search(body) and title.startswith(("一", "三")):
            continue
        order += 1
        results.append(
            ParsedEnglish(
                id=f"eng:sec-{_slug(title)}-{order}",
                title=title,
                body_md=body,
                sort_order=order,
                source_path=repo_relative,
            )
        )
    return results


def parse_skills(path: Path, *, repo_relative: str) -> list[ParsedSkill]:
    text = path.read_text(encoding="utf-8")
    results: list[ParsedSkill] = []
    order = 0

    # Core table (5 columns)
    core_section = text
    if "## 五、加分项" in text:
        core_section, bonus_section = text.split("## 五、加分项", 1)
    else:
        bonus_section = ""

    for match in SKILL_ROW.finditer(core_section):
        name = match.group("name").strip()
        if name in {"维度", "---"} or set(name) <= {"-"}:
            continue
        order += 1
        results.append(
            ParsedSkill(
                id=f"skill:{_slug(name)}",
                name=name,
                prompt=match.group("prompt").strip(),
                criterion=match.group("criterion").strip(),
                group_name="core",
                sort_order=order,
                source_path=repo_relative,
            )
        )

    for match in SKILL_BONUS_ROW.finditer(bonus_section):
        name = match.group("name").strip()
        if name in {"维度", "---"} or set(name) <= {"-"}:
            continue
        order += 1
        results.append(
            ParsedSkill(
                id=f"skill:bonus-{_slug(name)}",
                name=name,
                prompt=match.group("prompt").strip(),
                criterion="",
                group_name="bonus",
                sort_order=order,
                source_path=repo_relative,
            )
        )
    return results
