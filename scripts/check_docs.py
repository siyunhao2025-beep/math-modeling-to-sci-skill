#!/usr/bin/env python3
"""Static repository consistency checks for docs, prompts and CLI shims."""
from __future__ import annotations

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

ROOT = Path(common.REPO_ROOT)
SCRIPT_REF_RE = re.compile(r"(?<![\w.-])(scripts/[A-Za-z0-9_./-]+\.py)")
COMPAT_DIRS = ("ingest", "journals", "render", "validate")


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
        "references/publication-readiness-api-sources.md",
        "references/publication-readiness-suite.md",
        "prompts/00-extension-router.md",
        "prompts/08-sci-writing.md",
        "prompts/09-language-polish.md",
        "prompts/10-submission-journal-search.md",
        "prompts/11-publication-readiness-orchestrator.md",
        "prompts/12-reference-depth-audit.md",
        "prompts/13-journal-fit-deep.md",
        "prompts/14-claim-evidence-audit.md",
        "prompts/15-figure-table-audit.md",
        "prompts/16-reviewer-simulator.md",
        "prompts/17-submission-preflight.md",
        "prompts/18-methods-reporting-ethics.md",
        "prompts/shared/05-integrity-preservation.md",
        "prompts/shared/06-user-guidance-playbook.md",
        "config/publication-readiness.yaml",
        "config/schema/reviewer-simulation.schema.json",
        "config/schema/citation-support-audit.schema.json",
        "config/schema/submission-preflight.schema.json",
        "scripts/gates.py",
        "scripts/check_preservation.py",
        "scripts/audit_repo.py",
        "scripts/readiness/__init__.py",
        "scripts/readiness/utils.py",
        "scripts/readiness/reference_verifier.py",
        "scripts/readiness/journal_fit.py",
        "scripts/readiness/claim_evidence.py",
        "scripts/readiness/figure_table_audit.py",
        "scripts/readiness/compliance_audit.py",
        "scripts/readiness/language_check.py",
        "scripts/readiness/similarity_precheck.py",
        "scripts/readiness/template_fetch.py",
        "scripts/readiness/submission_preflight.py",
        "scripts/readiness/pipeline_bridge.py",
        "scripts/readiness/run_readiness.py",
        ".github/workflows/ci.yml",
        ".github/workflows/validate-skill.yml",
    ]
    for rel in required:
        if not exists(rel):
            errors.append(f"missing required repository path: {rel}")

    # Every literal scripts/foo.py path in Markdown must resolve. This replaces
    # the old one-off blacklist and catches new documentation drift immediately.
    for p in ROOT.rglob("*.md"):
        if any(part in {".git", "runs"} for part in p.parts):
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for ref in SCRIPT_REF_RE.findall(body):
            if not exists(ref):
                errors.append(f"{p.relative_to(ROOT)}: references nonexistent script {ref}")

    # Prompt inventory must include every actual prompt/shared file.
    prompt_readme = (ROOT / "prompts" / "README.md").read_text(encoding="utf-8")
    for p in (ROOT / "prompts").rglob("*.md"):
        if p.name == "README.md":
            continue
        if p.name not in prompt_readme:
            errors.append(f"prompts/README.md does not list {p.relative_to(ROOT / 'prompts')}")

    # The legacy subdirectories are compatibility CLI shims, not Python
    # packages. An __init__.py would create the import ambiguity reported in v2.
    for name in COMPAT_DIRS:
        flat = ROOT / "scripts" / f"{name}.py"
        shim = ROOT / "scripts" / name
        if not flat.is_file() or not shim.is_dir():
            errors.append(f"compatibility layout incomplete for scripts/{name}")
        if (shim / "__init__.py").exists():
            errors.append(
                f"scripts/{name}/ must remain package-less; __init__.py would shadow scripts/{name}.py"
            )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "--readiness" not in readme:
        errors.append("README.md does not document the S8 --readiness path")
    if "examples/input/sample-modeling-report.tex" not in readme:
        errors.append("README.md does not use the canonical sample-modeling-report.tex")

    legacy_alias = (ROOT / "examples" / "input" / "sample-model-report.tex").read_text(encoding="utf-8")
    if "COMPATIBILITY ALIAS" not in legacy_alias:
        errors.append("legacy sample-model-report.tex is not explicitly labelled as a compatibility alias")

    if errors:
        print("DOCUMENTATION / CONFIG CONSISTENCY: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("DOCUMENTATION / CONFIG CONSISTENCY: PASS")
    print(f"- configured stages checked: {len(pipeline.get('stages', []))}")
    print(f"- explicit required paths checked: {len(required)}")
    print("- markdown script references resolved")
    print("- prompt inventory synchronized")
    print("- compatibility CLI directories are package-less")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
