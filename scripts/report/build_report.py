#!/usr/bin/env python3
"""Compatibility CLI for building the conversion report."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _compat import copy_if_needed, load_flat_module  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=False)
    args = ap.parse_args()
    mod = load_flat_module("report")
    produced = mod.run(args.workdir)
    if args.out:
        copy_if_needed(produced, args.out)
        produced = args.out
    print(produced)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
