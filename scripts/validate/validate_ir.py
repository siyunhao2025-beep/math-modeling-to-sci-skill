#!/usr/bin/env python3
"""Compatibility CLI: validate manuscript IR against its JSON Schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True)
    args = ap.parse_args()
    data = common.load_json(args.ir)
    errors = common.validate_against_schema(
        data, common.repo_path("config", "schema", "manuscript.schema.json")
    )
    result = {"valid": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
