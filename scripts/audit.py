"""audit.py — 审计日志读写。append-only 的 audit.jsonl。

每条事件是一行 JSON。提供 AuditLogger 封装，便于各阶段统一追加。
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from common import save_json_atomic, sha256_of, utcnow_iso

SCHEMA = "config/schema/audit-log.schema.json"


class AuditLogger:
    """追加式审计日志。所有事件落盘到 workdir/audit.jsonl。"""

    def __init__(self, workdir: str):
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.path = os.path.join(workdir, "audit.jsonl")

    def log(self, event: str, stage: str = "S0", detail: Any = None,
            artifacts: Optional[list[dict]] = None, **extra: Any) -> dict:
        """追加一条事件，返回该事件 dict。"""
        record = {
            "event": event,
            "stage": stage,
            "at": utcnow_iso(),
        }
        if detail is not None:
            record["detail"] = detail
        if artifacts:
            record["artifacts"] = [
                {"path": a["path"], "sha256": sha256_of(a["path"])} for a in artifacts
            ]
        record.update(extra)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def set_env(self, env: dict) -> None:
        self.log("run_start", stage="S0", env=env, detail="environment probed")

    def read_all(self) -> list[dict]:
        if not os.path.isfile(self.path):
            return []
        out = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
