#!/usr/bin/env python3
"""Compatibility CLI for equation checks."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _validation_cli import manuscript_for_build, validation_module, write_checker_result  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    _, manuscript = manuscript_for_build(args.build)
    mod = validation_module()
    status, findings, skip = mod.checker_equations(manuscript)
    return write_checker_result("check_equations", status, findings, skip, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
