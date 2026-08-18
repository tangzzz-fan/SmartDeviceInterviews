"""
OTA/DFU 状态机仿真参考实现（Python = 真值）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OTAState:
    state: str = "idle"
    started: int = 0
    transfer_completed: int = 0
    verified: int = 0
    activated: int = 0
    progress: int = 0
    target_chunks: int = 8


def simulate(events: list[str], target_chunks: int = 8) -> dict[str, Any]:
    s = OTAState(target_chunks=target_chunks)

    for e in events:
        if e == "start" and s.state == "idle":
            s.state = "prepare"
            s.started = 1
            continue

        if s.state in ("prepare", "transferring"):
            if e in ("chunk_sent", "ack_received"):
                s.state = "transferring"
                if e == "ack_received":
                    s.progress += 1
                if s.progress >= s.target_chunks:
                    s.state = "verifying"
                    s.transfer_completed = 1
                continue
            if e in ("disconnect", "app_restart"):
                s.state = "failed_recoverable"
                continue

        if s.state == "verifying":
            if e == "verify_ok":
                s.state = "activating"
                s.verified = 1
                continue
            if e == "crc_error":
                s.state = "failed_recoverable"
                continue

        if s.state == "activating":
            if e == "activate_ok":
                s.state = "success"
                s.activated = 1
                continue
            if e == "disconnect":
                s.state = "failed_recoverable"
                continue

        if s.state == "failed_recoverable":
            if e == "resume_with_token":
                s.state = "transferring"
                continue
            if e == "fatal_error":
                s.state = "failed_fatal"
                continue

        if e == "fatal_error":
            s.state = "failed_fatal"

    return {
        "final_state": s.state,
        "funnel": {
            "started": s.started,
            "transfer_completed": s.transfer_completed,
            "verified": s.verified,
            "activated": s.activated,
        },
        "progress_chunks": s.progress,
    }
