#!/usr/bin/env python3
"""Compatibility-regression guard for legacy core and reviewed extensions.

This checker is intentionally *not* an anti-tamper or security mechanism.
With Git history available, two fixed commits are used as independent review
anchors:

- ``baseline_commit`` protects the original v1.0.0 repository surface;
- ``extension_baseline_commit`` governs already-existing post-v1.0 extension
  files so safety/readiness behavior cannot drift without an explicit reviewed
  allowlist reason.

New files are allowed. Without Git history, validation degrades to the protected
SKILL.md prefix plus required-path checks and clearly reports that limitation.
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


def _git_commit_available(repo_root: Path, commit: str | None) -> bool:
    if not commit or shutil.which("git") is None or not (repo_root / ".git").exists():
        return False
    return _git(repo_root, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0


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
        errors.append(f"SKILL.md legacy prefix changed: {actual} != {info['sha256']}")


def _verify_required_paths(repo_root: Path, manifest: dict, errors: list[str]) -> None:
    for group in ("required_paths_without_git_history", "required_extension_paths"):
        for rel in manifest.get(group, []):
            if not (repo_root / rel).exists():
                errors.append(f"Required path missing: {rel}")


def _verify_reason_coverage(manifest: dict, errors: list[str]) -> None:
    pairs = [
        ("approved_bugfix_paths", "approved_bugfix_reasons"),
        ("approved_extension_change_paths", "approved_extension_change_reasons"),
    ]
    for paths_key, reasons_key in pairs:
        approved = set(manifest.get(paths_key, []))
        reasons = manifest.get(reasons_key, {}) or {}
        missing = sorted(rel for rel in approved if not str(reasons.get(rel) or "").strip())
        if missing:
            errors.append(f"{paths_key} entries missing review reasons: {missing}")


def _verify_against_legacy_history(repo_root: Path, manifest: dict, errors: list[str]) -> dict:
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
        for rel in parts[1:]:
            if rel not in baseline_files:
                continue
            changed_baseline.append(rel)
            if status.startswith("D"):
                errors.append(f"Baseline file deleted: {rel}")
            elif rel == "SKILL.md":
                # The legacy prefix is checked byte-for-byte; additive content is allowed.
                continue
            elif rel not in approved:
                errors.append(
                    f"Unapproved change to baseline file: {rel} ({status}). "
                    "Add it only after review and record the reason."
                )

    return {
        "baseline_files": len(baseline_files),
        "changed_baseline_files": sorted(set(changed_baseline)),
    }


def _path_at_commit(repo_root: Path, commit: str, rel: str) -> bool:
    return _git(repo_root, "cat-file", "-e", f"{commit}:{rel}").returncode == 0


def _verify_extension_history(repo_root: Path, manifest: dict, errors: list[str]) -> dict:
    extension_baseline_commit = manifest.get("extension_baseline_commit")
    if not extension_baseline_commit:
        errors.append("extension_baseline_commit is missing")
        return {"extension_existing_files": 0, "changed_extension_files": []}

    approved = set(manifest.get("approved_extension_change_paths", []))
    governed = list(dict.fromkeys(manifest.get("required_extension_paths", [])))
    existing_at_anchor = [
        rel for rel in governed
        if _path_at_commit(repo_root, extension_baseline_commit, rel)
    ]
    changed: list[str] = []

    for rel in existing_at_anchor:
        proc = _git(repo_root, "diff", "--quiet", extension_baseline_commit, "--", rel)
        if proc.returncode == 0:
            continue
        if proc.returncode not in (0, 1):
            errors.append(f"Unable to diff extension path {rel}: {proc.stderr.strip()}")
            continue
        changed.append(rel)
        if not (repo_root / rel).exists():
            errors.append(f"Governed extension file deleted: {rel}")
        elif rel not in approved:
            errors.append(
                f"Unapproved change to governed extension file: {rel}. "
                "Add it to approved_extension_change_paths only after review and record the reason."
            )

    return {
        "extension_existing_files": len(existing_at_anchor),
        "changed_extension_files": sorted(set(changed)),
    }


def verify(repo_root: Path, manifest_path: Path) -> tuple[list[str], dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    details = {
        "history_mode": False,
        "extension_history_mode": False,
        "baseline_files": None,
        "changed_baseline_files": [],
        "extension_existing_files": None,
        "changed_extension_files": [],
    }

    _verify_skill_prefix(repo_root, manifest, errors)
    _verify_required_paths(repo_root, manifest, errors)
    _verify_reason_coverage(manifest, errors)

    baseline = manifest["baseline_commit"]
    if _git_commit_available(repo_root, baseline):
        details["history_mode"] = True
        details.update(_verify_against_legacy_history(repo_root, manifest, errors))

    ext = manifest.get("extension_baseline_commit")
    if _git_commit_available(repo_root, ext):
        details["extension_history_mode"] = True
        details.update(_verify_extension_history(repo_root, manifest, errors))

    return errors, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else repo_root / "config" / "preservation-manifest.json"
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
    print(f"- extension baseline commit: {manifest.get('extension_baseline_commit')}")
    print(f"- protected SKILL prefix bytes: {manifest['legacy_skill_prefix']['bytes']}")
    if details["history_mode"]:
        print(f"- Git-history baseline files checked: {details['baseline_files']}")
        print("- reviewed baseline files changed: " + (", ".join(details["changed_baseline_files"]) or "none"))
    else:
        print("- WARNING: legacy baseline Git history unavailable; only prefix/path checks were possible")
    if details["extension_history_mode"]:
        print(f"- governed extension files existing at anchor: {details['extension_existing_files']}")
        print("- reviewed extension files changed: " + (", ".join(details["changed_extension_files"]) or "none"))
    else:
        print("- WARNING: extension baseline Git history unavailable; extension change governance was partial")
    print("- scope: compatibility regression guard; not cryptographic tamper protection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
