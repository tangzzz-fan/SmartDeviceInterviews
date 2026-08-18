"""
生成 OTA/DFU 状态机仿真 golden。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ota_dfu_state_machine_prototype import simulate

CASE = "ota_dfu_state_machine"


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def build_dataset() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # 正常
    rows.append(
        {
            "id": "ota_001_happy_path",
            "case": CASE,
            "category": "normal",
            "input": {"events": ["start"] + ["ack_received"] * 8 + ["verify_ok", "activate_ok"], "target_chunks": 8},
            "expected": simulate(["start"] + ["ack_received"] * 8 + ["verify_ok", "activate_ok"], target_chunks=8),
        }
    )

    # 可恢复：断连后续传成功
    rows.append(
        {
            "id": "ota_002_disconnect_resume",
            "case": CASE,
            "category": "pathological",
            "input": {"events": ["start", "ack_received", "disconnect", "resume_with_token"] + ["ack_received"] * 7 + ["verify_ok", "activate_ok"], "target_chunks": 8},
            "expected": simulate(["start", "ack_received", "disconnect", "resume_with_token"] + ["ack_received"] * 7 + ["verify_ok", "activate_ok"], target_chunks=8),
        }
    )

    rows.append(
        {
            "id": "ota_003_crc_error_resume",
            "case": CASE,
            "category": "pathological",
            "input": {"events": ["start"] + ["ack_received"] * 8 + ["crc_error", "resume_with_token", "ack_received", "verify_ok", "activate_ok"], "target_chunks": 9},
            "expected": simulate(["start"] + ["ack_received"] * 8 + ["crc_error", "resume_with_token", "ack_received", "verify_ok", "activate_ok"], target_chunks=9),
        }
    )

    rows.append(
        {
            "id": "ota_004_fatal_after_disconnect",
            "case": CASE,
            "category": "pathological",
            "input": {"events": ["start", "ack_received", "disconnect", "fatal_error"], "target_chunks": 8},
            "expected": simulate(["start", "ack_received", "disconnect", "fatal_error"], target_chunks=8),
        }
    )

    rows.append(
        {
            "id": "ota_005_never_started",
            "case": CASE,
            "category": "pathological",
            "input": {"events": ["ack_received", "verify_ok"], "target_chunks": 8},
            "expected": simulate(["ack_received", "verify_ok"], target_chunks=8),
        }
    )

    # 扩展样本，保证病态占比高
    for i in range(6, 31):
        if i % 2 == 0:
            events = ["start", "ack_received", "app_restart", "resume_with_token"] + ["ack_received"] * 7 + ["verify_ok", "activate_ok"]
            category = "pathological"
            target = 8
        else:
            events = ["start"] + ["ack_received"] * 8 + ["verify_ok", "activate_ok"]
            category = "normal"
            target = 8
        rows.append(
            {
                "id": f"ota_{i:03d}_mix",
                "case": CASE,
                "category": category,
                "input": {"events": events, "target_chunks": target},
                "expected": simulate(events, target_chunks=target),
            }
        )
    return rows


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "golden" / CASE
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
    rows = build_dataset()
    for row in rows:
        (out / f"{row['id']}.json").write_text(_canonical_dump(row), encoding="utf-8")
    pathological = sum(1 for r in rows if r["category"] == "pathological")
    ratio = pathological / len(rows)
    print(f"wrote {len(rows)} records to {out} (pathological_ratio={ratio:.2%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
