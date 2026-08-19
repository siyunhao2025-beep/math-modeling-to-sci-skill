#!/usr/bin/env python3
"""Run deterministic S8 readiness checks from an existing S1-S7 workdir.

Only ``--workdir`` is required. The bridge automatically resolves IR, BibTeX,
the selected S4 journal, ISSN and build paths when those artifacts exist.
Current official Aims & Scope / article-type evidence is never guessed: provide
it through the standard journal-evidence files or optional CLI overrides.
Semantic citation support, visual scientific judgment and Reviewer Simulator
remain explicit Agent tasks, so preflight stays conservative until they exist.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.pipeline_bridge import run_from_workdir  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="S8 Publication Readiness Suite")
    ap.add_argument("--workdir", required=True, help="existing S1-S7 work directory")
    ap.add_argument("--target-journal", help="override the S4-selected journal name/id")

    # Advanced overrides. They are intentionally optional because most should be
    # resolved from the pipeline workdir rather than retyped by the user.
    ap.add_argument("--ir")
    ap.add_argument("--bib")
    ap.add_argument("--manuscript", help="IR JSON or manuscript text")
    ap.add_argument("--journal-name")
    ap.add_argument("--issn")
    ap.add_argument("--aims-scope-file")
    ap.add_argument("--scope-source-url")
    ap.add_argument("--article-types-file")
    ap.add_argument("--article-type")
    ap.add_argument("--article-type-source-url")
    ap.add_argument("--build-tex")
    ap.add_argument("--source-root")

    ap.add_argument("--mailto", default=os.getenv("CROSSREF_MAILTO"))
    ap.add_argument("--s2-api-key", default=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
    ap.add_argument("--ncbi-api-key", default=os.getenv("NCBI_API_KEY"))
    ap.add_argument("--languagetool-server")
    ap.add_argument("--with-similarity-precheck", action="store_true")
    args = ap.parse_args()

    overrides = {
        key: value
        for key, value in {
            "ir": args.ir,
            "bib": args.bib,
            "manuscript": args.manuscript,
            "journal_name": args.journal_name,
            "issn": args.issn,
            "aims_scope_file": args.aims_scope_file,
            "scope_source_url": args.scope_source_url,
            "article_types_file": args.article_types_file,
            "article_type": args.article_type,
            "article_type_source_url": args.article_type_source_url,
            "build_tex": args.build_tex,
            "source_root": args.source_root,
        }.items()
        if value is not None
    }

    result = run_from_workdir(
        args.workdir,
        target_journal=args.target_journal,
        with_similarity_precheck=args.with_similarity_precheck,
        languagetool_server=args.languagetool_server,
        mailto=args.mailto,
        s2_api_key=args.s2_api_key,
        ncbi_api_key=args.ncbi_api_key,
        overrides=overrides,
    )

    summary = result.get("bridge_summary") or {}
    print(
        "S8 deterministic bridge complete. "
        f"Preflight={result['status']}; "
        f"executed={len(summary.get('executed', []))}; "
        f"deferred={summary.get('deferred_count', 0)}; "
        f"tool_errors={summary.get('tool_error_count', 0)}."
    )
    print(
        "Agent-only citation-support, semantic journal/claim review, visual "
        "scientific review and Reviewer Simulator must be completed before the "
        "strongest READY_FOR_HUMAN_SUBMISSION_CHECK status can be trusted."
    )
    return 0 if result["status"] == "READY_FOR_HUMAN_SUBMISSION_CHECK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
