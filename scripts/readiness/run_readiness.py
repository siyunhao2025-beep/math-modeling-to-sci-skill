#!/usr/bin/env python3
"""Run all deterministic S8 readiness checks in one command.

Semantic citation support, visual scientific judgment and Reviewer Simulator
remain Agent tasks. This runner prepares their evidence artifacts and then
executes preflight; preflight is expected to remain BLOCKED/AUTHOR_ACTION_REQUIRED
until the Agent artifacts are completed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import os

from readiness import claim_evidence, compliance_audit, figure_table_audit, journal_fit
from readiness import language_check, reference_verifier, similarity_precheck, submission_preflight


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--ir", required=True)
    ap.add_argument("--bib", required=True)
    ap.add_argument("--manuscript", required=True, help="IR JSON or manuscript text for fit/compliance/language checks")
    ap.add_argument("--journal-name", required=True)
    ap.add_argument("--issn", required=True)
    ap.add_argument("--aims-scope-file", required=True)
    ap.add_argument("--scope-source-url", required=True)
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

    out = Path(args.workdir) / "08-readiness"
    out.mkdir(parents=True, exist_ok=True)

    reference_verifier.run(
        args.bib,
        str(out / "reference-verification.json"),
        str(out / "references.clean.bib"),
        mailto=args.mailto,
        s2_key=args.s2_api_key,
        ncbi_key=args.ncbi_api_key,
    )
    journal_fit.run(
        args.manuscript,
        args.journal_name,
        args.issn,
        args.aims_scope_file,
        str(out / "journal-fit.json"),
        article_types_file=args.article_types_file,
        article_type=args.article_type,
        scope_source_url=args.scope_source_url,
        article_type_source_url=args.article_type_source_url,
        mailto=args.mailto,
    )
    claim_evidence.run(args.ir, str(out / "claim-evidence-audit.json"))
    figure_table_audit.run(args.ir, str(out / "figure-table-audit.json"), args.build_tex, args.source_root)
    compliance_audit.run(args.manuscript, str(out / "compliance-audit.json"))
    language_check.run(args.manuscript, str(out / "language-audit.json"), args.languagetool_server)
    if args.with_similarity_precheck:
        similarity_precheck.run(args.manuscript, str(out / "similarity-precheck.json"), args.s2_api_key)

    result = submission_preflight.run(
        args.workdir,
        str(out / "submission-preflight.json"),
        str(out / "submission-preflight.md"),
    )
    print(
        "Deterministic readiness pass complete. "
        f"Preflight={result['status']}. Complete Agent citation-support, visual review "
        "and Reviewer Simulator artifacts before final human-submission check."
    )
    return 0 if result["status"] == "READY_FOR_HUMAN_SUBMISSION_CHECK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
