"""Seed closed-book speak prompts mapped from SmartGlass → Nirva bank."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models import SpeakDraft, SpeakPrompt, SpeakStatus

# Glass id → Nirva practice targets. References are Nirva-oriented, not Glass JD copy.
SPEAK_SEEDS: list[dict] = [
    {
        "id": "speak:position",
        "glass_source_id": "k-position",
        "title": "本场定位（Founding iOS）",
        "ask": "一句话说清：你是什么岗、擅长什么、为何匹配 Nirva Founding iOS。",
        "seconds": "15 秒",
        "linked_question_ids": "F1,F8,F9",
        "linked_whiteboard_ids": "",
        "reference": (
            "偏智能穿戴端侧的 founding iOS：擅长 BLE 连接态、OTA、联调归因与稳定性基建；"
            "能在模糊需求里把协议、状态机和可观测性先立起来。不是算法训练岗，是把设备链路做成可交付产品的客户端 owner。"
        ),
        "sort_order": 1,
    },
    {
        "id": "speak:intro-90",
        "glass_source_id": "k-intro-90",
        "title": "自我介绍 90 秒",
        "ask": "开场完整版：经验锚点 → 硬件/BLE 证据 → founding 动机。",
        "seconds": "90 秒",
        "linked_question_ids": "F1,F11",
        "linked_whiteboard_ids": "",
        "reference": (
            "结构：身份与年限 → 1–2 个设备/连接项目（Ready≠didConnect、OTA、联调）→ "
            "稳定性或架构演进一点 → 为什么 founding（0→1 基建、ownership）。"
            "英文版见题库 F11；数字必须是你真实项目里的。"
        ),
        "sort_order": 2,
    },
    {
        "id": "speak:ble-90",
        "glass_source_id": "k-ble-90",
        "title": "蓝牙我做过什么",
        "ask": "把扫描/连接/Ready/断连恢复挂到同一套方法上，90 秒。",
        "seconds": "90 秒",
        "linked_question_ids": "B1,B2,B7,B14",
        "linked_whiteboard_ids": "WB1",
        "reference": (
            "Core Bluetooth 全链路：扫描有界 → 连接 → 服务发现 → notify → 应用层握手才 Ready。"
            "断连分用户/系统/链路；只有链路走有限退避。指标按固件与 iOS 版本切片。"
            "对照白板 WB1；深挖题 B2/B7/B14。"
        ),
        "sort_order": 3,
    },
    {
        "id": "speak:ready-30",
        "glass_source_id": "",
        "title": "Ready ≠ didConnect",
        "ask": "为什么不能在 didConnect 就发业务命令？30 秒结论先行。",
        "seconds": "30 秒",
        "linked_question_ids": "B2,E3",
        "linked_whiteboard_ids": "WB1",
        "reference": (
            "didConnect 只表示链路层连上；业务 Ready = 发现目标服务/特征 + CCCD 订阅成功 + "
            "可选应用层握手。提前发命令会静默失败或竞态。状态机上 Connected ≠ Ready。"
        ),
        "sort_order": 4,
    },
    {
        "id": "speak:ota-90",
        "glass_source_id": "k-jd-90",
        "title": "OTA 怎么讲（JD 串讲切片）",
        "ask": "下载校验、分片、设备确认、防砖边界：你负责什么、固件负责什么。",
        "seconds": "90 秒",
        "linked_question_ids": "B9,C5,C7",
        "linked_whiteboard_ids": "WB2",
        "reference": (
            "App：包获取与校验、传输窗口/重试、进度与失败可恢复、激活确认；"
            "固件：双槽/回滚、写 flash、防砖策略。发完不算成功，设备确认才算。"
            "版本矩阵与 EVT/DVT 节奏见 C5/C7；画 WB2。"
        ),
        "sort_order": 5,
    },
    {
        "id": "speak:debug-30",
        "glass_source_id": "k-case-30",
        "title": "联调/难题开场",
        "ask": "「遇到难题怎么解决」先给结论与定界，再等人追问。",
        "seconds": "30 秒",
        "linked_question_ids": "C2,C10,B14,E4",
        "linked_whiteboard_ids": "WB3",
        "reference": (
            "先结论：问题落在 App / 固件 / 协议 / 环境哪一层。"
            "方法：复现条件 → 分层证据（日志/抓包/固件版本）→ 单一变量对照 → 防回归埋点。"
            "对照白板 WB3；事故流程见 E4。"
        ),
        "sort_order": 6,
    },
    {
        "id": "speak:audio-honest",
        "glass_source_id": "k-audio",
        "title": "音频/数据面口径（诚实）",
        "ask": "被问音频怎么走：先讲你真实做过的；区分 Glass 双链路与 Nirva 加分项。",
        "seconds": "30 秒",
        "linked_question_ids": "B5",
        "linked_whiteboard_ids": "WB7",
        "reference": (
            "若做过：按带宽/时延切通道（控制面 BLE vs 大数据面），讲吞吐、背压、时间戳。"
            "Glass 材料口径是 BLE 控制 + WiFi PCM——见专栏 SmartGlass，勿与 Nirva 题库混成同一 ID。"
            "若未做过连续 PCM：承认边界，落到传感器批量同步（B5）与白板 WB7 的设计题。"
        ),
        "sort_order": 7,
    },
    {
        "id": "speak:asr-boundary",
        "glass_source_id": "k-asr-honest",
        "title": "AI/云能力边界",
        "ask": "模型/SDK 是黑盒时，你怎么定界与降级？",
        "seconds": "30 秒",
        "linked_question_ids": "AI2,AI6,AI5",
        "linked_whiteboard_ids": "",
        "reference": (
            "先承认：引擎内部未改。App 负责契约、编排、超时、降级与证据链打包。"
            "异常分段：端侧 / 网络 / 云端。验证 AI 产出见 AI2；接口边界见 AI6。"
        ),
        "sort_order": 8,
    },
    {
        "id": "speak:unknown",
        "glass_source_id": "k-unknown",
        "title": "不会时怎么接",
        "ask": "被问没测过的数字、记不准的字段、引擎内部。",
        "seconds": "15 秒",
        "linked_question_ids": "F7,C3",
        "linked_whiteboard_ids": "",
        "reference": (
            "这块我当时没有做到 X 内部。App/联调侧我会用 Y 埋点或对照实验先定界；"
            "具体字段需要对文档/日志。接着给一个你做过的相邻证据，避免空转。"
        ),
        "sort_order": 9,
    },
    {
        "id": "speak:weakness",
        "glass_source_id": "k-weakness",
        "title": "短板怎么答",
        "ask": "不把自己说成「不会硬件」；转到岗位核心与学习曲线。",
        "seconds": "30 秒",
        "linked_question_ids": "F10,C9,F8",
        "linked_whiteboard_ids": "",
        "reference": (
            "承认边界（例如未写 RTOS / 未主导某平台），立刻转到：协议联调、状态机、可观测性、"
            "与固件协作——这是 founding iOS 的核心。前六个月计划见 F8。"
        ),
        "sort_order": 10,
    },
    {
        "id": "speak:sync-offline",
        "glass_source_id": "",
        "title": "离线同步不丢不乱",
        "ask": "端侧队列、幂等、冲突：90 秒能画能讲。",
        "seconds": "90 秒",
        "linked_question_ids": "E2,A6,A7",
        "linked_whiteboard_ids": "WB6",
        "reference": (
            "有界队列 + 命令生命周期；write 成功 ≠ 执行成功；冲突以设备权威或向量时钟策略说清。"
            "前后台恢复见 A7/WB4；画 WB6。"
        ),
        "sort_order": 11,
    },
    {
        "id": "speak:power",
        "glass_source_id": "",
        "title": "功耗预算口述",
        "ask": "App 侧能控什么、如何测、如何和固件对齐。",
        "seconds": "60 秒",
        "linked_question_ids": "B13,D3",
        "linked_whiteboard_ids": "WB5",
        "reference": (
            "扫描有界、连接参数、后台策略、通知频率；用 Energy/Instruments + 场景标签对齐固件电流曲线。"
            "对照 WB5；BLE 功耗题 B13。"
        ),
        "sort_order": 12,
    },
]


def seed_speak_prompts(session: Session) -> int:
    count = 0
    for item in SPEAK_SEEDS:
        existing = session.get(SpeakPrompt, item["id"])
        fields = {k: v for k, v in item.items() if k != "id"}
        if existing is None:
            session.add(SpeakPrompt(id=item["id"], **fields))
            count += 1
        else:
            for k, v in fields.items():
                setattr(existing, k, v)
            session.add(existing)
            count += 1
        if session.get(SpeakDraft, item["id"]) is None:
            session.add(
                SpeakDraft(prompt_id=item["id"], status=SpeakStatus.drafting)
            )
    session.commit()
    return count


def ensure_speak_seeded(session: Session) -> None:
    row = session.exec(select(SpeakPrompt).limit(1)).first()
    if row is None:
        seed_speak_prompts(session)
