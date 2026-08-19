#!/usr/bin/env python3
"""Compatibility CLI for template acquisition with explicit fallback disclosure.

This deterministic command never claims that a bundled skeleton is an official
journal template. Network/official-template acquisition is handled by the
agent/web layer; this CLI creates an auditable fallback when necessary.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = common.load_yaml(common.repo_path("config", "journals.yaml"))
    journal = next(
        (
            j for j in cfg.get("journals", [])
            if j.get("name", "").lower() == args.journal.lower()
            or j.get("id", "").lower() == args.journal.lower()
        ),
        None,
    )
    publisher = (journal or {}).get("publisher")
    bundle = {
        "Elsevier": "elsevier-generic",
        "IEEE": "ieee-generic",
        "Springer": "springer-generic",
    }.get(publisher)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    copied_from = None
    if bundle:
        src = Path(common.repo_path("assets", "templates", bundle))
        if src.is_dir():
            for item in src.iterdir():
                target = out / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
            copied_from = str(src.relative_to(Path(common.REPO_ROOT)))

    manifest = {
        "journal": args.journal,
        "status": "degraded",
        "official": False,
        "source": copied_from or "no bundled publisher skeleton available",
        "note": (
            "This command did not download or verify an official journal template. "
            "Replace this fallback with the current official template before submission."
        ),
    }
    with open(out / "MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
