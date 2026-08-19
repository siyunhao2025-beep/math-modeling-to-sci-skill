#!/usr/bin/env python3
"""Static repository consistency checks for documented/configured paths.

This catches the class of failure where README/SKILL/pipeline configuration
references commands or resources that do not exist in the repository.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

ROOT = Path(common.REPO_ROOT)


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def main() -> int:
    errors: list[str] = []
    pipeline = common.load_yaml(common.repo_path("config", "pipeline.yaml"))

    for stage in pipeline.get("stages", []):
        prompt = stage.get("prompt")
        if prompt and not exists(prompt):
            errors.append(f"{stage.get('id')}: missing prompt {prompt}")
        for script in stage.get("scripts", []) or []:
            if not exists(script):
                errors.append(f"{stage.get('id')}: missing configured script {script}")

    required = [
        "examples/input/sample-modeling-report.tex",
        "examples/input/sample-model-report.tex",
        "docs/architecture.md",
        "references/troubleshooting.md",
        "prompts/00-extension-router.md",
        "prompts/08-sci-writing.md",
        "prompts/09-language-polish.md",
        "prompts/10-submission-journal-search.md",
        "prompts/shared/05-integrity-preservation.md",
        "scripts/gates.py",
        "scripts/check_preservation.py",
        ".github/workflows/ci.yml",
        ".github/workflows/validate-skill.yml",
    ]
    for rel in required:
        if not exists(rel):
            errors.append(f"missing required repository path: {rel}")

    # Guard the most visible README/SKILL command drift without trying to parse
    # every markdown code block as shell syntax.
    text_files = ["SKILL.md", "README.md", "CONTRIBUTING.md", "CHANGELOG.md"]
    known_bad = [
        # Entries may be added here when a deprecated path must remain forbidden.
        "scripts/ingest/parse_word.py",
    ]
    for rel in text_files:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"missing documentation file: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        for bad in known_bad:
            if bad in text:
                errors.append(f"{rel}: references deprecated/nonexistent path {bad}")

    if errors:
        print("DOCUMENTATION / CONFIG CONSISTENCY: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("DOCUMENTATION / CONFIG CONSISTENCY: PASS")
    print(f"- configured stages checked: {len(pipeline.get('stages', []))}")
    print(f"- explicit required paths checked: {len(required)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
