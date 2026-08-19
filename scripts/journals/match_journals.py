#!/usr/bin/env python3
"""Compatibility CLI for deterministic journal matching."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _compat import copy_if_needed, load_flat_module, workdir_from_output  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assessment", required=True)
    ap.add_argument("--ir", required=False, help="accepted for the documented S4 contract")
    ap.add_argument("--out", required=True)
    ap.add_argument("--journal", default=None)
    args = ap.parse_args()
    mod = load_flat_module("journals")
    wd = workdir_from_output(args.out, "04-journals")
    produced = mod.run(args.assessment, wd, target_journal=args.journal)
    copy_if_needed(produced, args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
