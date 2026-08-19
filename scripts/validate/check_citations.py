#!/usr/bin/env python3
"""Compatibility CLI for bidirectional citation checks."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _validation_cli import bib_keys, manuscript_for_build, validation_module, write_checker_result  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verify-doi", action="store_true",
                    help="reserved for the agent/web verification layer; no DOI is silently marked verified")
    args = ap.parse_args()
    _, manuscript = manuscript_for_build(args.build)
    mod = validation_module()
    status, findings, skip = mod.checker_citations(manuscript, bib_keys(args.build))
    if args.verify_doi:
        skip = (skip + "; " if skip else "") + (
            "DOI network verification is not performed by this deterministic wrapper; "
            "use prompts/02-academic-rewrite.md or the journal/citation web verification workflow."
        )
    return write_checker_result("check_citations", status, findings, skip, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
