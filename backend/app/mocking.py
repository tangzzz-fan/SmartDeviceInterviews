"""Mock interview templates and pass/fail scoring (平均分≥4 且无单题≤2)."""

from __future__ import annotations

import json
from typing import Any

# Aligned with 综合版/08_模拟面试脚本.md
MOCK_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "R1": [
        {"id": "R1-open", "label": "开场电梯陈述（90 秒）"},
        {"id": "R1-A", "label": "系统设计 · BLE OTA 主线"},
        {"id": "R1-B", "label": "Swift 并发快问快答"},
        {"id": "R1-C", "label": "性能与后台"},
        {"id": "R1-D", "label": "项目深挖（旗舰故事）"},
    ],
    "R2": [
        {"id": "R2-motivation", "label": "开场与动机"},
        {"id": "R2-ownership", "label": "Ownership 深挖"},
        {"id": "R2-english", "label": "英文环节"},
        {"id": "R2-closing", "label": "收尾（教训 / AI / 反问）"},
    ],
    "phone": [
        {"id": "PH-intro", "label": "60–90 秒介绍"},
        {"id": "PH-why", "label": "为什么 founding"},
        {"id": "PH-en", "label": "英文协作举例"},
        {"id": "PH-gap", "label": "加分项缺口话术"},
    ],
}


def template_items(round_key: str) -> list[dict[str, Any]]:
    items = MOCK_TEMPLATES.get(round_key, [])
    return [{"id": i["id"], "label": i["label"], "score": None} for i in items]


def compute_result(scores: list[dict[str, Any]]) -> tuple[float | None, bool]:
    """Return (average, passed). Pass: avg >= 4 and no scored item <= 2."""
    values = [int(s["score"]) for s in scores if s.get("score") is not None]
    if not values:
        return None, False
    average = round(sum(values) / len(values), 2)
    passed = average >= 4 and min(values) > 2
    return average, passed


def dumps_scores(scores: list[dict[str, Any]]) -> str:
    return json.dumps(scores, ensure_ascii=False)


def loads_scores(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
