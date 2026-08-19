#!/usr/bin/env python3
"""Verify the additive-integration preservation contract.

All files present at baseline are protected byte-for-byte except SKILL.md.
SKILL.md must retain the complete baseline file as an exact prefix; only
content after that prefix may be added.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(repo_root: Path, manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    skill_info = manifest["legacy_skill_prefix"]
    skill_path = repo_root / "SKILL.md"
    if not skill_path.exists():
        errors.append("SKILL.md is missing")
    else:
        data = skill_path.read_bytes()
        n = int(skill_info["bytes"])
        if len(data) < n:
            errors.append(
                f"SKILL.md is shorter than the protected legacy prefix: {len(data)} < {n}"
            )
        else:
            prefix_hash = sha256_bytes(data[:n])
            if prefix_hash != skill_info["sha256"]:
                errors.append(
                    "SKILL.md legacy prefix changed: "
                    f"{prefix_hash} != {skill_info['sha256']}"
                )

    for rel, expected in manifest["protected_files"].items():
        path = repo_root / rel
        if not path.exists():
            errors.append(f"Protected file missing: {rel}")
            continue
        actual_bytes = path.read_bytes()
        actual_hash = sha256_bytes(actual_bytes)
        if actual_hash != expected["sha256"]:
            errors.append(
                f"Protected file changed: {rel}: "
                f"{actual_hash} != {expected['sha256']}"
            )
        if len(actual_bytes) != int(expected["bytes"]):
            errors.append(
                f"Protected file size changed: {rel}: "
                f"{len(actual_bytes)} != {expected['bytes']}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest = (
        args.manifest.resolve()
        if args.manifest
        else repo_root / "config" / "preservation-manifest.json"
    )

    errors = verify(repo_root, manifest)
    if errors:
        print("PRESERVATION CHECK: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    print("PRESERVATION CHECK: PASS")
    print(f"- baseline commit: {manifest_data['baseline_commit']}")
    print(f"- protected files: {len(manifest_data['protected_files'])}")
    print(
        "- protected SKILL prefix bytes: "
        f"{manifest_data['legacy_skill_prefix']['bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
