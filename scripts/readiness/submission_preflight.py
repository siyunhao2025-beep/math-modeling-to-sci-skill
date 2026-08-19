#!/usr/bin/env python3
"""One-click publication readiness preflight.

Aggregates S6 validation plus post-S6 readiness artifacts. The strongest
positive label is READY_FOR_HUMAN_SUBMISSION_CHECK: no deterministic/Agent tool
can guarantee acceptance or replace the journal's submission portal validation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import load_json, save_json  # noqa: E402

REQUIRED = {
    "validation": "06-validate/validation-final.json",
    "references": "08-readiness/reference-verification.json",
    "citation_support": "08-readiness/citation-support-audit.json",
    "journal_fit": "08-readiness/journal-fit.json",
    "claim_evidence": "08-readiness/claim-evidence-audit.json",
    "figure_table": "08-readiness/figure-table-audit.json",
    "compliance": "08-readiness/compliance-audit.json",
    "reviewer": "08-readiness/reviewer-simulation.json",
}
OPTIONAL = {
    "language": "08-readiness/language-audit.json",
    "similarity": "08-readiness/similarity-precheck.json",
    "template": "08-readiness/template-provenance.json",
    "latex_compile": "08-readiness/latex-compile.json",
}


def _load(root: Path, rel: str):
    p = root / rel
    return load_json(p) if p.is_file() else None


def _latex_status(validation: dict, standalone: dict | None) -> str:
    if standalone and standalone.get("checker") == "latex_compile_check":
        return standalone.get("status") or "missing"
    for c in validation.get("checkers", []):
        if c.get("name") == "latex_compile_check":
            return c.get("status") or "missing"
    return "missing"


def run(workdir: str, out_json: str, out_md: str | None = None) -> dict:
    root = Path(workdir)
    data = {k: _load(root, rel) for k, rel in {**REQUIRED, **OPTIONAL}.items()}
    blockers = []
    warnings = []

    for key, rel in REQUIRED.items():
        if data[key] is None:
            blockers.append({"code": "ARTIFACT_MISSING", "area": key, "detail": rel})

    v = data.get("validation") or {}
    if (v.get("summary") or {}).get("error_count", 1) != 0:
        blockers.append({"code": "S6_ERRORS", "area": "validation", "detail": (v.get("summary") or {}).get("unresolved_error_ids", [])})

    latex_build = (root / "05-template" / "build" / "main.tex").is_file()
    if latex_build:
        latex = _latex_status(v, data.get("latex_compile"))
        if latex != "pass":
            blockers.append({"code": "LATEX_NOT_COMPILED", "area": "validation", "detail": f"latex_compile_check={latex}"})

    refs = data.get("references") or {}
    if refs.get("blockers"):
        blockers.append({"code": "REFERENCE_VERIFICATION", "area": "references", "detail": refs.get("blockers")})

    cs = data.get("citation_support") or {}
    bad_cites = [x for x in cs.get("citations", []) if x.get("status") in ("CONTRADICTS", "DOES_NOT_SUPPORT")]
    unknown_cites = [x for x in cs.get("citations", []) if x.get("status") == "CANNOT_VERIFY"]
    if bad_cites:
        blockers.append({"code": "CITATION_SUPPORT", "area": "citation_support", "detail": [x.get("id") for x in bad_cites]})
    if unknown_cites:
        warnings.append({"code": "CITATION_SUPPORT_AUTHOR_CHECK", "area": "citation_support", "detail": [x.get("id") for x in unknown_cites]})
    if cs.get("blockers"):
        blockers.append({"code": "CITATION_SUPPORT_DECLARED_BLOCKERS", "area": "citation_support", "detail": cs.get("blockers")})

    jf = data.get("journal_fit") or {}
    if jf.get("blockers"):
        blockers.append({"code": "JOURNAL_FIT", "area": "journal_fit", "detail": jf.get("blockers")})
    if (jf.get("baseline_fit_score_0_100") or 0) < 55:
        warnings.append({"code": "JOURNAL_FIT_LOW", "area": "journal_fit", "detail": jf.get("baseline_fit_score_0_100")})
    semantic_fit = (jf.get("agent_semantic_review") or {}).get("decision")
    if semantic_fit in ("WEAK_FIT", "BLOCKED_NEEDS_CURRENT_EVIDENCE"):
        blockers.append({"code": "JOURNAL_SEMANTIC_FIT", "area": "journal_fit", "detail": semantic_fit})
    elif semantic_fit is None:
        warnings.append({"code": "JOURNAL_SEMANTIC_REVIEW_PENDING", "area": "journal_fit", "detail": "Agent semantic journal-fit decision missing"})

    ce = data.get("claim_evidence") or {}
    if ce.get("blockers"):
        blockers.append({"code": "CLAIM_EVIDENCE", "area": "claim_evidence", "detail": ce.get("blockers")})
    semantic_bad = [c for c in ce.get("claims", []) if c.get("agent_semantic_status") in ("UNSUPPORTED", "CONTRADICTED", "OUT_OF_SCOPE_GENERALIZATION") and c.get("risk") == "high"]
    semantic_pending = [c for c in ce.get("claims", []) if c.get("agent_semantic_status") in (None, "PENDING")]
    if semantic_bad:
        blockers.append({"code": "SEMANTIC_CLAIM_FAILURE", "area": "claim_evidence", "detail": [c.get("id") for c in semantic_bad]})
    if semantic_pending:
        warnings.append({"code": "SEMANTIC_CLAIM_REVIEW_PENDING", "area": "claim_evidence", "detail": [c.get("id") for c in semantic_pending[:20]]})

    ft = data.get("figure_table") or {}
    if ft.get("blockers"):
        blockers.append({"code": "FIGURE_TABLE", "area": "figure_table", "detail": ft.get("blockers")})
    if ft.get("visual_scientific_review") not in ("PASS", "PASS_WITH_WARNINGS"):
        blockers.append({"code": "VISUAL_REVIEW_PENDING", "area": "figure_table", "detail": ft.get("visual_scientific_review")})

    comp = data.get("compliance") or {}
    if comp.get("blockers"):
        blockers.append({"code": "COMPLIANCE", "area": "compliance", "detail": comp.get("blockers")})
    if any(g.get("official_checklist_status") != "PASS" for g in comp.get("recommended_reporting_guidelines", [])):
        warnings.append({"code": "REPORTING_GUIDELINE_REVIEW", "area": "compliance", "detail": comp.get("recommended_reporting_guidelines", [])})

    rev = data.get("reviewer") or {}
    unresolved = [c for c in rev.get("comments", []) if c.get("status", "OPEN") != "RESOLVED" and c.get("severity") in ("blocker", "major")]
    if unresolved:
        blockers.append({"code": "REVIEWER_SIMULATOR_MAJOR", "area": "reviewer", "detail": [c.get("id") for c in unresolved]})
    if rev and len(rev.get("comments", [])) < 3:
        warnings.append({"code": "REVIEWER_SIMULATION_SHALLOW", "area": "reviewer", "detail": "fewer than 3 substantive comments"})

    lang = data.get("language") or {}
    if lang.get("blockers"):
        blockers.append({"code": "LANGUAGE_OVERCLAIM", "area": "language", "detail": lang.get("blockers")})

    sim = data.get("similarity") or {}
    if sim.get("high_flags"):
        warnings.append({"code": "SIMILARITY_REVIEW", "area": "similarity", "detail": [m.get("title") for m in sim.get("high_flags", [])[:5]]})

    template = data.get("template")
    if latex_build:
        if not template or template.get("status") != "VERIFIED_OFFICIAL_SOURCE" or not template.get("integrity_ok", False):
            blockers.append({"code": "OFFICIAL_TEMPLATE_PROVENANCE", "area": "template", "detail": "LaTeX manuscript lacks verified official-template provenance"})

    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "AUTHOR_ACTION_REQUIRED"
    else:
        status = "READY_FOR_HUMAN_SUBMISSION_CHECK"

    result = {
        "schema_version": "1.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "workdir": str(root),
        "status": status,
        "blockers": blockers,
        "warnings": warnings,
        "artifact_presence": {k: data[k] is not None for k in data},
        "disclaimer": "This preflight reduces preventable submission failures; it does not predict or guarantee editorial acceptance.",
    }
    save_json(out_json, result)

    if out_md:
        lines = ["# Submission Preflight", "", f"**Status: {status}**", "", "## Blockers"]
        lines += ([f"- `{x['code']}` ({x['area']}): {x['detail']}" for x in blockers] or ["- None"])
        lines += ["", "## Warnings"]
        lines += ([f"- `{x['code']}` ({x['area']}): {x['detail']}" for x in warnings] or ["- None"])
        lines += ["", "> This is a readiness audit, not an acceptance guarantee."]
        Path(out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--out-md", default=None)
    args = ap.parse_args()
    out_json = args.out_json or str(Path(args.workdir) / "08-readiness" / "submission-preflight.json")
    out_md = args.out_md or str(Path(args.workdir) / "08-readiness" / "submission-preflight.md")
    result = run(args.workdir, out_json, out_md)
    print(f"{result['status']} blockers={len(result['blockers'])} warnings={len(result['warnings'])}")
    return 0 if result["status"] == "READY_FOR_HUMAN_SUBMISSION_CHECK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
