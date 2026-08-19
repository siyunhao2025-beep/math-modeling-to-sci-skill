#!/usr/bin/env python3
"""Compatibility CLI for LaTeX / zipped LaTeX-project parsing."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _compat import copy_if_needed, load_flat_module, workdir_from_output  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    workdir = workdir_from_output(args.out, "01-parse")

    if args.input.lower().endswith(".zip"):
        import project_ingest
        produced = project_ingest.run(args.input, workdir)
    else:
        ingest = load_flat_module("ingest")
        produced = ingest.run(args.input, workdir, source_format="latex")

    copy_if_needed(produced, args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
