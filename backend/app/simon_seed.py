"""Seed Simon learning goal trees (分解 · 反馈环)."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models import SimonGoal, SimonNode, SimonNodeProgress, SimonNodeStatus

SIMON_SEEDS: list[dict] = [
    {
        "id": "simon:ble-ready",
        "title": "BLE Ready 能讲清",
        "description": "能在 2 分钟内讲清 Ready≠didConnect、断连分类、重连预算与指标切片。",
        "sort_order": 1,
        "nodes": [
            {
                "id": "simon:ble-ready:ready-def",
                "title": "Ready 定义",
                "description": "服务发现 + notify + 握手，缺一不可。",
                "linked_question_ids": "B2",
                "linked_whiteboard_ids": "WB1",
                "sort_order": 1,
            },
            {
                "id": "simon:ble-ready:disconnect",
                "title": "断连三分类",
                "description": "用户 / 系统 / 链路，只有链路走有限退避。",
                "linked_question_ids": "B7",
                "linked_whiteboard_ids": "WB1",
                "sort_order": 2,
            },
            {
                "id": "simon:ble-ready:budget",
                "title": "重连预算",
                "description": "次数、退避、前后台差异；预算耗尽回 Idle。",
                "linked_question_ids": "B7,E3",
                "linked_whiteboard_ids": "WB1",
                "sort_order": 3,
            },
            {
                "id": "simon:ble-ready:metrics",
                "title": "指标切片",
                "description": "连接成功率按固件/iOS 版本切片，不凭感觉。",
                "linked_question_ids": "B3,B14",
                "linked_whiteboard_ids": "",
                "sort_order": 4,
            },
        ],
    },
    {
        "id": "simon:five-layer",
        "title": "五层答题能脱口",
        "description": "任意 P0 题：结论 → 机制 → 案例 → 取舍 → 指标。",
        "sort_order": 2,
        "nodes": [
            {
                "id": "simon:five-layer:conclusion",
                "title": "第一句是结论",
                "description": "90 秒内先抛结论，再展开。",
                "linked_question_ids": "A1,B1",
                "linked_whiteboard_ids": "",
                "sort_order": 1,
            },
            {
                "id": "simon:five-layer:mechanism",
                "title": "有机制无形容词",
                "description": "能画/能说清状态迁移或调用链。",
                "linked_question_ids": "A7,B2",
                "linked_whiteboard_ids": "WB1,WB3",
                "sort_order": 2,
            },
            {
                "id": "simon:five-layer:evidence",
                "title": "案例或缺口话术",
                "description": "有数字，或诚实承认边界。",
                "linked_question_ids": "C2,F7",
                "linked_whiteboard_ids": "",
                "sort_order": 3,
            },
            {
                "id": "simon:five-layer:metric",
                "title": "指标或说明为何没有",
                "description": "能量化则量化；不能则说明补数计划。",
                "linked_question_ids": "D1,A3",
                "linked_whiteboard_ids": "",
                "sort_order": 4,
            },
        ],
    },
]


def seed_simon_trees(session: Session) -> int:
    """Upsert goals/nodes; do not overwrite progress. Returns node count."""
    count = 0
    for goal in SIMON_SEEDS:
        existing = session.get(SimonGoal, goal["id"])
        if existing is None:
            session.add(
                SimonGoal(
                    id=goal["id"],
                    title=goal["title"],
                    description=goal["description"],
                    sort_order=goal["sort_order"],
                )
            )
        else:
            existing.title = goal["title"]
            existing.description = goal["description"]
            existing.sort_order = goal["sort_order"]
            session.add(existing)

        for node in goal["nodes"]:
            count += 1
            row = session.get(SimonNode, node["id"])
            fields = {
                "goal_id": goal["id"],
                "title": node["title"],
                "description": node["description"],
                "linked_question_ids": node["linked_question_ids"],
                "linked_whiteboard_ids": node["linked_whiteboard_ids"],
                "sort_order": node["sort_order"],
            }
            if row is None:
                session.add(SimonNode(id=node["id"], **fields))
                if session.get(SimonNodeProgress, node["id"]) is None:
                    session.add(
                        SimonNodeProgress(node_id=node["id"], status=SimonNodeStatus.todo)
                    )
            else:
                for k, v in fields.items():
                    setattr(row, k, v)
                session.add(row)
                if session.get(SimonNodeProgress, node["id"]) is None:
                    session.add(
                        SimonNodeProgress(node_id=node["id"], status=SimonNodeStatus.todo)
                    )
    session.commit()
    return count


def ensure_simon_seeded(session: Session) -> None:
    existing = session.exec(select(SimonGoal)).first()
    if existing is None:
        seed_simon_trees(session)
