"""
生成 CoreML 在线漂移监控报告 golden。
"""

from __future__ import annotations

import json
from pathlib import Path

from .coreml_drift_prototype import run


def main() -> int:
    report = run()
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "golden" / "coreml_drift_monitoring"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "report.json"
    out_path.write_text(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    if not all(report["pass"].values()):
        print("ERROR: drift-monitoring expectations not met")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
