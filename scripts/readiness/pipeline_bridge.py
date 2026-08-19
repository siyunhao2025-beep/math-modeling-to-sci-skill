#!/usr/bin/env python3
"""Bridge S1-S7 workdir artifacts into the S8 Publication Readiness Suite.

This module makes S8 usable from an existing pipeline run without forcing the
user to manually re-type paths that the workflow already knows. It is
conservative by design: unavailable network evidence, missing official journal
scope/article-type evidence, or missing Agent-only artifacts are surfaced as
explicit blockers/warnings rather than guessed or silently skipped.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from readiness import claim_evidence, compliance_audit, figure_table_audit, journal_fit
from readiness import language_check, reference_verifier, similarity_precheck, submission_preflight
from readiness.utils import load_json, save_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def _load_optional(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = load_json(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _selected_recommendation(jm: dict, target_journal: str | None = None) -> dict:
    recs = jm.get("recommendations") or []
    if target_journal:
        wanted = target_journal.strip().lower()
        for rec in recs:
            if str(rec.get("name") or "").lower() == wanted or str(rec.get("journal_id") or "").lower() == wanted:
                return rec
    return recs[0] if recs else {}


def _evidence_meta(root: Path) -> dict:
    candidates = [
        root / "04-journals" / "journal-evidence" / "target-journal.json",
        root / "04-journals" / "journal-evidence" / "evidence.json",
        root / "08-readiness" / "journal-evidence.json",
    ]
    for path in candidates:
        data = _load_optional(path)
        if data:
            data["_source_file"] = str(path)
            return data
    return {}


def resolve_inputs(
    workdir: str,
    *,
    target_journal: str | None = None,
    ir: str | None = None,
    bib: str | None = None,
    manuscript: str | None = None,
    journal_name: str | None = None,
    issn: str | None = None,
    aims_scope_file: str | None = None,
    scope_source_url: str | None = None,
    article_types_file: str | None = None,
    article_type: str | None = None,
    article_type_source_url: str | None = None,
    build_tex: str | None = None,
    source_root: str | None = None,
) -> dict[str, Any]:
    root = Path(workdir)
    jm_path = root / "04-journals" / "journal-match.json"
    jm = _load_optional(jm_path)
    rec = _selected_recommendation(jm, target_journal)
    ev = _evidence_meta(root)

    resolved_ir = Path(ir) if ir else _first_existing(
        root / "02-rewrite" / "manuscript.rewritten.json",
        root / "01-parse" / "manuscript.ir.json",
    )
    resolved_bib = Path(bib) if bib else _first_existing(
        root / "05-template" / "build" / "references.bib",
        root / "02-rewrite" / "references.bib",
    )
    resolved_manuscript = Path(manuscript) if manuscript else resolved_ir
    resolved_build_tex = Path(build_tex) if build_tex else _first_existing(
        root / "05-template" / "build" / "main.tex",
    )

    evidence_dir = root / "04-journals" / "journal-evidence"
    resolved_scope = Path(aims_scope_file) if aims_scope_file else _first_existing(
        evidence_dir / "aims-scope.txt",
        evidence_dir / "aims-and-scope.txt",
        evidence_dir / "target-aims-scope.txt",
    )
    resolved_types = Path(article_types_file) if article_types_file else _first_existing(
        evidence_dir / "article-types.txt",
        evidence_dir / "target-article-types.txt",
    )

    return {
        "workdir": str(root),
        "ir": str(resolved_ir) if resolved_ir else None,
        "bib": str(resolved_bib) if resolved_bib else None,
        "manuscript": str(resolved_manuscript) if resolved_manuscript else None,
        "journal_name": journal_name or ev.get("journal_name") or rec.get("name"),
        "issn": issn or ev.get("issn") or rec.get("issn"),
        "aims_scope_file": str(resolved_scope) if resolved_scope else None,
        "scope_source_url": scope_source_url or ev.get("scope_source_url") or ev.get("aims_scope_source_url"),
        "article_types_file": str(resolved_types) if resolved_types else None,
        "article_type": article_type or ev.get("article_type"),
        "article_type_source_url": article_type_source_url or ev.get("article_type_source_url"),
        "build_tex": str(resolved_build_tex) if resolved_build_tex else None,
        "source_root": source_root or str(root / "00-input"),
        "journal_match": str(jm_path) if jm_path.is_file() else None,
        "journal_evidence_meta": ev.get("_source_file"),
    }


def _write_missing_reference(out: Path, detail: str) -> None:
    save_json(out / "reference-verification.json", {
        "schema_version": "1.0",
        "verified_at": _now(),
        "summary": {"total": 0, "verified": 0, "blocked": 1, "clean_bib_policy": "strict"},
        "references": [],
        "blockers": [{"key": "ALL", "status": "unverified", "reason": detail}],
        "ready": False,
        "degraded": True,
    })


def _write_missing_journal_fit(out: Path, inputs: dict, missing: list[str]) -> None:
    save_json(out / "journal-fit.json", {
        "schema_version": "1.0",
        "journal": inputs.get("journal_name"),
        "issn": inputs.get("issn"),
        "article_type": inputs.get("article_type"),
        "article_type_verified": False,
        "allowed_article_types": [],
        "official_evidence": {
            "aims_scope_source_url": inputs.get("scope_source_url"),
            "article_type_source_url": inputs.get("article_type_source_url"),
            "aims_scope_file": inputs.get("aims_scope_file"),
        },
        "recent_corpus": {"source": "not run", "months": 12, "count": 0, "mean_similarity": 0.0, "top10_mean_similarity": 0.0, "items": []},
        "scope_similarity": 0.0,
        "baseline_fit_score_0_100": 0.0,
        "risks": [],
        "blockers": [f"readiness bridge missing: {item}" for item in missing],
        "ready_for_agent_semantic_review": False,
        "important_limit": "Current official Aims & Scope/article-type evidence is required; the bridge will not infer it from a submission URL or seed database.",
    })


def run_from_workdir(
    workdir: str,
    *,
    target_journal: str | None = None,
    with_similarity_precheck: bool = False,
    languagetool_server: str | None = None,
    mailto: str | None = None,
    s2_api_key: str | None = None,
    ncbi_api_key: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict:
    """Run deterministic S8 checks using artifacts already present in workdir.

    Agent-only artifacts (citation semantic support, visual scientific review,
    reviewer simulation, semantic journal-fit/claim review) are intentionally
    not fabricated. Their absence remains visible to submission_preflight.
    """
    root = Path(workdir)
    out = root / "08-readiness"
    out.mkdir(parents=True, exist_ok=True)
    inputs = resolve_inputs(workdir, target_journal=target_journal, **(overrides or {}))
    save_json(out / "resolved-inputs.json", inputs)

    executed: list[str] = []
    deferred: list[dict] = []
    errors: list[dict] = []

    bib = inputs.get("bib")
    if bib and Path(bib).is_file():
        try:
            reference_verifier.run(
                bib,
                str(out / "reference-verification.json"),
                str(out / "references.clean.bib"),
                mailto=mailto or os.getenv("CROSSREF_MAILTO"),
                s2_key=s2_api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY"),
                ncbi_key=ncbi_api_key or os.getenv("NCBI_API_KEY"),
            )
            executed.append("reference_verifier")
        except Exception as exc:
            errors.append({"module": "reference_verifier", "error": str(exc)})
            _write_missing_reference(out, f"reference verifier failed: {exc}")
    else:
        deferred.append({"module": "reference_verifier", "reason": "no BibTeX artifact found"})
        _write_missing_reference(out, "no BibTeX artifact found in S2/S5 outputs")

    jf_required = {
        "manuscript": inputs.get("manuscript"),
        "journal_name": inputs.get("journal_name"),
        "issn": inputs.get("issn"),
        "aims_scope_file": inputs.get("aims_scope_file"),
        "scope_source_url": inputs.get("scope_source_url"),
        "article_types_file": inputs.get("article_types_file"),
        "article_type": inputs.get("article_type"),
        "article_type_source_url": inputs.get("article_type_source_url"),
    }
    missing_jf = [key for key, value in jf_required.items() if not value]
    if not missing_jf:
        try:
            journal_fit.run(
                inputs["manuscript"],
                inputs["journal_name"],
                inputs["issn"],
                inputs["aims_scope_file"],
                str(out / "journal-fit.json"),
                article_types_file=inputs["article_types_file"],
                article_type=inputs["article_type"],
                scope_source_url=inputs["scope_source_url"],
                article_type_source_url=inputs["article_type_source_url"],
                mailto=mailto or os.getenv("CROSSREF_MAILTO"),
            )
            executed.append("journal_fit")
        except Exception as exc:
            errors.append({"module": "journal_fit", "error": str(exc)})
            _write_missing_journal_fit(out, inputs, [f"journal_fit failed: {exc}"])
    else:
        deferred.append({"module": "journal_fit", "reason": "current official evidence incomplete", "missing": missing_jf})
        _write_missing_journal_fit(out, inputs, missing_jf)

    ir = inputs.get("ir")
    if ir and Path(ir).is_file():
        for name, fn, args in [
            ("claim_evidence", claim_evidence.run, (ir, str(out / "claim-evidence-audit.json"))),
            ("figure_table_audit", figure_table_audit.run, (ir, str(out / "figure-table-audit.json"), inputs.get("build_tex"), inputs.get("source_root"))),
        ]:
            try:
                fn(*args)
                executed.append(name)
            except Exception as exc:
                errors.append({"module": name, "error": str(exc)})
    else:
        deferred.append({"module": "claim_evidence/figure_table_audit", "reason": "IR artifact missing"})

    manuscript = inputs.get("manuscript")
    if manuscript and Path(manuscript).is_file():
        try:
            compliance_audit.run(manuscript, str(out / "compliance-audit.json"))
            executed.append("compliance_audit")
        except Exception as exc:
            errors.append({"module": "compliance_audit", "error": str(exc)})
        try:
            language_check.run(manuscript, str(out / "language-audit.json"), languagetool_server)
            executed.append("language_check")
        except Exception as exc:
            errors.append({"module": "language_check", "error": str(exc)})
        if with_similarity_precheck:
            try:
                similarity_precheck.run(manuscript, str(out / "similarity-precheck.json"), s2_api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
                executed.append("similarity_precheck")
            except Exception as exc:
                errors.append({"module": "similarity_precheck", "error": str(exc)})
    else:
        deferred.append({"module": "compliance/language", "reason": "manuscript/IR artifact missing"})

    # Agent-only evidence is intentionally not auto-created. Scaffolds would
    # look like completed audits and could let a naive aggregator pass them.
    for artifact, purpose in [
        ("citation-support-audit.json", "Agent must verify whether each citation actually supports the manuscript claim"),
        ("reviewer-simulation.json", "Agent must perform substantive reviewer simulation/rebuttal loop"),
    ]:
        if not (out / artifact).is_file():
            deferred.append({"artifact": artifact, "reason": purpose})

    save_json(out / "readiness-run.json", {
        "schema_version": "1.0",
        "ran_at": _now(),
        "mode": "pipeline-bridge",
        "executed": executed,
        "deferred": deferred,
        "errors": errors,
        "truthfulness_note": "Deferred checks remain unresolved. This file does not certify submission readiness.",
    })

    preflight = submission_preflight.run(
        workdir,
        str(out / "submission-preflight.json"),
        str(out / "submission-preflight.md"),
    )
    preflight["bridge_summary"] = {
        "executed": executed,
        "deferred_count": len(deferred),
        "tool_error_count": len(errors),
    }
    save_json(out / "submission-preflight.json", preflight)
    return preflight
