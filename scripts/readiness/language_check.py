#!/usr/bin/env python3
"""Publication-language audit with optional LanguageTool server integration.

No public LanguageTool endpoint is assumed. Supply --server (for example a local
LanguageTool HTTP server) to enable grammar diagnostics. Internal checks focus on
scientific-register risks and never rewrite protected scientific content.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.compliance_audit import text_from  # noqa: E402
from readiness.utils import save_json  # noqa: E402

AI_BOILERPLATE = [
    r"it is worth noting that",
    r"plays? a crucial role",
    r"provides? valuable insights",
    r"comprehensive understanding",
    r"it is important to note that",
    r"in today's rapidly evolving",
]
OVERCLAIM = [r"\bdefinitively\b", r"\bcompletely proves?\b", r"\bproves? that\b", r"\bundeniably\b", r"\bperfect(?:ly)?\b"]
DOUBLE_HEDGE = [r"may possibly", r"might potentially", r"could perhaps", r"may suggest that .* may"]


def run(manuscript: str, out: str, server: str | None = None, language: str = "en-US") -> dict:
    text = text_from(manuscript)
    findings = []
    for code, pats, severity in [
        ("AI_STYLE", AI_BOILERPLATE, "warning"),
        ("OVERCLAIM", OVERCLAIM, "blocker"),
        ("DOUBLE_HEDGE", DOUBLE_HEDGE, "warning"),
    ]:
        for pat in pats:
            for m in re.finditer(pat, text, re.I | re.S):
                findings.append({"code": code, "severity": severity, "match": m.group(0)[:160], "offset": m.start()})

    lt = {"status": "not_run", "matches": []}
    if server:
        try:
            r = requests.post(server.rstrip("/") + "/v2/check", data={"language": language, "text": text}, timeout=45)
            r.raise_for_status()
            data = r.json()
            lt = {"status": "pass", "matches": data.get("matches", [])}
        except Exception as exc:
            lt = {"status": "error", "error": str(exc), "matches": []}

    blockers = [f for f in findings if f["severity"] == "blocker"]
    result = {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "internal_findings": findings,
        "languagetool": lt,
        "summary": {"blockers": len(blockers), "warnings": sum(1 for x in findings if x["severity"] == "warning"), "languagetool_matches": len(lt.get("matches", []))},
        "blockers": blockers,
        "guardrails": ["do not change numbers, units, formulas, citations or claim strength during automatic language repair", "LanguageTool diagnostics are suggestions, not scientific validation"],
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--server")
    ap.add_argument("--language", default="en-US")
    args = ap.parse_args()
    result = run(args.manuscript, args.out, args.server, args.language)
    print(f"blockers={result['summary']['blockers']} LT={result['languagetool']['status']} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
