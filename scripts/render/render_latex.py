#!/usr/bin/env python3
"""Compatibility CLI for rendering manuscript IR to LaTeX."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _compat import copy_if_needed, load_flat_module, workdir_from_output  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True)
    ap.add_argument("--template", required=False,
                    help="template directory; deterministic renderer records fallback separately")
    ap.add_argument("--out", required=True,
                    help="output build directory or main.tex path")
    args = ap.parse_args()

    out_path = Path(args.out)
    main_target = out_path / "main.tex" if out_path.suffix == "" else out_path
    wd = workdir_from_output(str(main_target), "05-template")
    mod = load_flat_module("render")
    produced = mod.run(args.ir, wd, journal_match_path=None)
    copy_if_needed(produced, str(main_target))
    print(main_target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
