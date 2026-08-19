#!/usr/bin/env python3
"""Build a claim–evidence ledger from manuscript IR.

This is a conservative structural audit. It identifies claim-like sentences and
whether they contain an explicit evidence link (citation, figure/table/equation
reference, or an internal result marker). Semantic support is evaluated by the
Agent in prompts/14-claim-evidence-audit.md.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import load_json, save_json  # noqa: E402

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\\])")
CIT_RE = re.compile(r"\\cite\w*\{[^}]+\}|\([A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s*\d{4}[a-z]?\)")
OBJ_RE = re.compile(r"(?:Fig(?:ure)?\.?|Table|Eq(?:uation)?\.?)\s*~?\\?ref?\{?[^\s,.;)]*|\\(?:ref|autoref|cref)\{[^}]+\}", re.I)
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:\s*[%KmsnTPaHz°])?")
CAUSAL_RE = re.compile(r"\b(causes?|drives?|results? in|leads? to|due to|because of|explains?|responsible for|induces?|produces?)\b", re.I)
INTERP_RE = re.compile(r"\b(suggests?|indicates?|implies?|consistent with|may reflect|likely|possibly|potentially)\b", re.I)
COMPAR_RE = re.compile(r"\b(higher|lower|larger|smaller|stronger|weaker|increase[sd]?|decrease[sd]?|improv(?:e|ed|ement)|outperform(?:s|ed)?)\b", re.I)


def _sentences(text: str) -> list[str]:
    text = " ".join((text or "").split())
    return [s.strip() for s in SENTENCE_RE.split(text) if s.strip()]


def classify(sentence: str, role: str) -> tuple[str, str]:
    if CAUSAL_RE.search(sentence):
        return "causal", "high"
    if NUMBER_RE.search(sentence) and role in ("results", "experiments", "discussion", "conclusion"):
        return "quantitative_result", "high"
    if COMPAR_RE.search(sentence):
        return "comparative", "medium"
    if INTERP_RE.search(sentence):
        return "interpretation", "medium"
    if role in ("introduction", "related_work", "discussion"):
        return "knowledge_or_context", "medium"
    return "descriptive", "low"


def run(ir_path: str, out: str) -> dict:
    ir = load_json(ir_path)
    claims = []
    cid = 0
    for sec in ir.get("sections", []):
        role = sec.get("semantic_role") or "unclassified"
        for bi, block in enumerate(sec.get("blocks", []), 1):
            if block.get("type") != "paragraph" or not block.get("text"):
                continue
            block_citations = list(block.get("citations") or [])
            for si, sent in enumerate(_sentences(block["text"]), 1):
                ctype, risk = classify(sent, role)
                # Ignore low-risk methods/descriptive prose unless it contains a number/comparison.
                if risk == "low" and not NUMBER_RE.search(sent) and not COMPAR_RE.search(sent):
                    continue
                cid += 1
                has_citation = bool(block_citations or CIT_RE.search(sent))
                has_object = bool(OBJ_RE.search(sent))
                internal_result = role in ("results", "experiments") and bool(NUMBER_RE.search(sent) or has_object)
                evidence_links = []
                if has_citation:
                    evidence_links.append("citation")
                if has_object:
                    evidence_links.append("figure_table_equation")
                if internal_result:
                    evidence_links.append("internal_result")
                supported_structurally = bool(evidence_links)
                severity = "blocker" if (risk == "high" and not supported_structurally) else ("warning" if not supported_structurally else "info")
                claims.append({
                    "id": f"claim-{cid}",
                    "section_id": sec.get("id"),
                    "section_role": role,
                    "block_index": bi,
                    "sentence_index": si,
                    "text": sent,
                    "claim_type": ctype,
                    "risk": risk,
                    "evidence_links": evidence_links,
                    "structurally_supported": supported_structurally,
                    "severity": severity,
                    "agent_semantic_status": "PENDING",
                    "note": "Structural evidence link only; semantic correctness must be checked by the Agent.",
                })
    blockers = [c for c in claims if c["severity"] == "blocker"]
    warnings = [c for c in claims if c["severity"] == "warning"]
    result = {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "input_ir": ir_path,
        "summary": {
            "claims_reviewed": len(claims),
            "structural_blockers": len(blockers),
            "warnings": len(warnings),
            "semantic_review_pending": len(claims),
        },
        "claims": claims,
        "blockers": [c["id"] for c in blockers],
        "ready_for_agent_semantic_audit": True,
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = run(args.ir, args.out)
    print(f"claims={result['summary']['claims_reviewed']} blockers={result['summary']['structural_blockers']} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
