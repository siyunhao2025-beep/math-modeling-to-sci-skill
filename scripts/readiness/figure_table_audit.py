#!/usr/bin/env python3
"""Audit figures/tables for source, caption, mapping and in-text references."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import ir_text, load_json, save_json  # noqa: E402


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def run(ir_path: str, out: str, build_tex: str | None = None, source_root: str | None = None) -> dict:
    ir = load_json(ir_path)
    text = ir_text(ir)
    build = Path(build_tex).read_text(encoding="utf-8") if build_tex and Path(build_tex).is_file() else ""
    root = Path(source_root) if source_root else Path(ir_path).resolve().parent
    items = []

    def add(kind: str, obj: dict):
        oid = obj.get("id") or "unknown"
        caption = _norm(obj.get("caption") or "")
        refs = obj.get("referenced_in") or []
        issues = []
        source = obj.get("path") if kind == "figure" else None
        if not caption:
            issues.append({"code": "CAPTION_MISSING", "severity": "blocker"})
        elif len(caption.split()) < 4:
            issues.append({"code": "CAPTION_TOO_SHORT", "severity": "warning"})
        if not refs:
            issues.append({"code": "NOT_REFERENCED_IN_IR", "severity": "warning"})
        if kind == "figure":
            if not source:
                issues.append({"code": "FIGURE_SOURCE_MISSING", "severity": "blocker"})
            elif source_root:
                p = (root / source).resolve() if not Path(source).is_absolute() else Path(source)
                if not p.exists():
                    issues.append({"code": "FIGURE_FILE_NOT_FOUND", "severity": "blocker", "detail": str(p)})
        else:
            rows = obj.get("rows") or []
            header = obj.get("header") or []
            if not rows and not header:
                issues.append({"code": "TABLE_EMPTY", "severity": "blocker"})
        # Build mapping is a second independent signal.
        if build:
            label_variants = [f"{kind[:3]}:{oid}", oid]
            if not any(v in build for v in label_variants):
                issues.append({"code": "BUILD_MAPPING_NOT_FOUND", "severity": "blocker"})
        items.append({"kind": kind, "id": oid, "caption": caption, "source": source, "referenced_in": refs, "issues": issues})

    for f in ir.get("figures", []):
        add("figure", f)
    for t in ir.get("tables", []):
        add("table", t)

    blockers = []
    warnings = []
    for item in items:
        for issue in item["issues"]:
            target = blockers if issue["severity"] == "blocker" else warnings
            target.append({"object": item["id"], "kind": item["kind"], **issue})
    result = {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "input_ir": ir_path,
        "build_tex": build_tex,
        "summary": {"figures": len(ir.get("figures", [])), "tables": len(ir.get("tables", [])), "blockers": len(blockers), "warnings": len(warnings)},
        "objects": items,
        "blockers": blockers,
        "warnings": warnings,
        "visual_scientific_review": "PENDING_AGENT_REVIEW",
        "note": "This deterministic pass checks object integrity/mapping. The Agent must still inspect axes, units, legends, uncertainty, visual honesty and caption self-containment.",
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--build-tex")
    ap.add_argument("--source-root")
    args = ap.parse_args()
    result = run(args.ir, args.out, args.build_tex, args.source_root)
    print(f"figures={result['summary']['figures']} tables={result['summary']['tables']} blockers={result['summary']['blockers']} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
