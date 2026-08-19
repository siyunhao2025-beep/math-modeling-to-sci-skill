#!/usr/bin/env python3
"""Compatibility-regression guard for the original v1.0.0 workflow.

This checker is intentionally *not* described as an anti-tamper or security
mechanism. With Git history available, the baseline commit is the independent
source of truth: baseline files may not disappear, and changes to baseline
files must be explicitly allowlisted as reviewed bug fixes. Without Git
history, the checker falls back to the protected SKILL.md prefix plus required
path checks and prints that the verification is partial.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_baseline_available(repo_root: Path, baseline: str) -> bool:
    if shutil.which("git") is None or not (repo_root / ".git").exists():
        return False
    proc = _git(repo_root, "cat-file", "-e", f"{baseline}^{{commit}}")
    return proc.returncode == 0


def _verify_skill_prefix(repo_root: Path, manifest: dict, errors: list[str]) -> None:
    info = manifest["legacy_skill_prefix"]
    path = repo_root / "SKILL.md"
    if not path.exists():
        errors.append("SKILL.md is missing")
        return
    data = path.read_bytes()
    n = int(info["bytes"])
    if len(data) < n:
        errors.append(f"SKILL.md shorter than protected legacy prefix: {len(data)} < {n}")
        return
    actual = sha256_bytes(data[:n])
    if actual != info["sha256"]:
        errors.append(
            "SKILL.md legacy prefix changed: "
            f"{actual} != {info['sha256']}"
        )


def _verify_required_paths(repo_root: Path, manifest: dict, errors: list[str]) -> None:
    for group in ("required_paths_without_git_history", "required_extension_paths"):
        for rel in manifest.get(group, []):
            if not (repo_root / rel).exists():
                errors.append(f"Required path missing: {rel}")


def _verify_against_git_history(repo_root: Path, manifest: dict, errors: list[str]) -> dict:
    baseline = manifest["baseline_commit"]
    approved = set(manifest.get("approved_bugfix_paths", []))

    ls = _git(repo_root, "ls-tree", "-r", "--name-only", baseline)
    if ls.returncode != 0:
        errors.append(f"Unable to list baseline tree: {ls.stderr.strip()}")
        return {"baseline_files": 0, "changed_baseline_files": []}
    baseline_files = {line.strip() for line in ls.stdout.splitlines() if line.strip()}

    for rel in sorted(baseline_files):
        if not (repo_root / rel).exists():
            errors.append(f"Baseline file deleted: {rel}")

    diff = _git(repo_root, "diff", "--name-status", baseline, "--")
    if diff.returncode != 0:
        errors.append(f"Unable to diff against baseline: {diff.stderr.strip()}")
        return {"baseline_files": len(baseline_files), "changed_baseline_files": []}

    changed_baseline: list[str] = []
    for line in diff.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        paths = parts[1:]
        # For renames/copies, inspect all paths that belonged to the baseline.
        for rel in paths:
            if rel not in baseline_files:
                continue
            changed_baseline.append(rel)
            if status.startswith("D"):
                errors.append(f"Baseline file deleted: {rel}")
            elif rel == "SKILL.md":
                # Prefix integrity is verified independently; additive extension is allowed.
                continue
            elif rel not in approved:
                errors.append(
                    f"Unapproved change to baseline file: {rel} ({status}). "
                    "Add to approved_bugfix_paths only after review."
                )

    return {
        "baseline_files": len(baseline_files),
        "changed_baseline_files": sorted(set(changed_baseline)),
    }


def verify(repo_root: Path, manifest_path: Path) -> tuple[list[str], dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    details = {"history_mode": False, "baseline_files": None, "changed_baseline_files": []}

    _verify_skill_prefix(repo_root, manifest, errors)
    _verify_required_paths(repo_root, manifest, errors)

    baseline = manifest["baseline_commit"]
    if _git_baseline_available(repo_root, baseline):
        details["history_mode"] = True
        details.update(_verify_against_git_history(repo_root, manifest, errors))
    return errors, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest_path = (
        args.manifest.resolve()
        if args.manifest
        else repo_root / "config" / "preservation-manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors, details = verify(repo_root, manifest_path)

    if errors:
        print("PRESERVATION / COMPATIBILITY CHECK: FAIL")
        for item in errors:
            print(f"- {item}")
        print("NOTE: this is a regression guard, not an anti-tamper security guarantee.")
        return 1

    print("PRESERVATION / COMPATIBILITY CHECK: PASS")
    print(f"- baseline commit: {manifest['baseline_commit']}")
    print(f"- protected SKILL prefix bytes: {manifest['legacy_skill_prefix']['bytes']}")
    if details["history_mode"]:
        print(f"- Git-history baseline files checked: {details['baseline_files']}")
        print(
            "- reviewed baseline files changed in this version: "
            + (", ".join(details["changed_baseline_files"]) or "none")
        )
    else:
        print("- WARNING: baseline Git history unavailable; only prefix/path checks were possible")
    print("- scope: compatibility regression guard; not cryptographic tamper protection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
