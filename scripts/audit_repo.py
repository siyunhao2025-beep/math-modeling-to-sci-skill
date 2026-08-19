#!/usr/bin/env python3
"""Executable regression audit for the 18 risks recorded in the review register.

This script turns the external review questions into repository checks. It is
intentionally conservative: PASS means the specific regression is guarded by
code/docs/tests, not that the scientific workflow is perfect or acceptance is
predicted. It performs no network calls.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REF_RE = re.compile(r"(?<![\w.-])(scripts/[A-Za-z0-9_./-]+\.py)")
COMPAT = ("ingest", "journals", "render", "validate")


def text(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def result(risk: str, ok: bool, evidence: str, impact: str, fix: str = "") -> dict:
    return {
        "risk": risk,
        "status": "PASS" if ok else "FAIL",
        "evidence": evidence,
        "impact": impact,
        "fix": fix if not ok else "—",
    }


def markdown_script_refs() -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for p in ROOT.rglob("*.md"):
        if any(part in {".git", "runs"} for part in p.parts):
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for ref in SCRIPT_REF_RE.findall(body):
            if "..." in ref:  # illustrative placeholder, not a concrete command path
                continue
            refs.append((str(p.relative_to(ROOT)), ref))
    return refs


def audit() -> list[dict]:
    out: list[dict] = []
    runner = text("scripts/run_pipeline.py")
    rr = text("scripts/readiness/run_readiness.py")
    readme = text("README.md")
    prompt_readme = text("prompts/README.md")
    changelog = text("CHANGELOG.md")
    router = text("prompts/00-extension-router.md")
    manifest = json.loads(text("config/preservation-manifest.json") or "{}")

    # V2-F1 — S8 must be reachable from the main runtime and user docs.
    ok = all(x in runner for x in ("run_readiness_from_workdir", "--readiness", "[S8]")) and "--readiness" in readme
    out.append(result("V2-F1", ok,
        "run_pipeline.py imports/calls readiness bridge; README documents --readiness",
        "Without this, publication-readiness is an orphan feature.",
        "Wire pipeline_bridge into S7 pre-report execution and document it."))

    # V2-F2 — compatibility directories may coexist only as package-less CLI shims.
    collisions_ok = True
    details = []
    for name in COMPAT:
        flat = ROOT / "scripts" / f"{name}.py"
        directory = ROOT / "scripts" / name
        package_init = directory / "__init__.py"
        this_ok = flat.is_file() and directory.is_dir() and not package_init.exists()
        collisions_ok &= this_ok
        details.append(f"{name}: flat={flat.is_file()} shim_dir={directory.is_dir()} package={package_init.exists()}")
    out.append(result("V2-F2", collisions_ok, "; ".join(details),
        "A same-name importable package could shadow the canonical flat runtime module.",
        "Keep shim directories package-less or rename them; add namespace regression tests."))

    # V1-F1 — every concrete documented scripts/*.py reference must exist.
    bad_refs = [(src, ref) for src, ref in markdown_script_refs() if not exists(ref)]
    out.append(result("V1-F1", not bad_refs, f"missing documented script refs={bad_refs[:10]}",
        "Copy-paste commands would fail with No such file.",
        "Fix the documented path or add a real compatibility CLI."))

    # V1-F2 — canonical example + explicitly-labelled legacy alias.
    alias = text("examples/input/sample-model-report.tex")
    ok = exists("examples/input/sample-modeling-report.tex") and exists("examples/input/sample-model-report.tex") and "COMPATIBILITY ALIAS" in alias
    out.append(result("V1-F2", ok, "canonical sample-modeling-report.tex + labelled legacy alias",
        "Two unexplained near-identical filenames confuse users and tests.",
        "Keep the legacy path only as an explicit compatibility alias; use canonical name in new docs."))

    # V1-F3 — executable quality-gate path + runtime regression test.
    ok = "GateEvaluator" in runner and ".evaluate(gate_id)" in runner and exists("tests/test_runtime_gates.py")
    out.append(result("V1-F3", ok, "GateEvaluator.evaluate + test_runtime_gates.py",
        "A decorative gate lets failed science/validation flow into output.",
        "Evaluate G1-G6 and stop/retry/degrade according to configuration."))

    # V2-F3 — one canonical implementation; compatibility commands must delegate.
    delegate_ok = True
    shim_hits = []
    for rel in ["scripts/ingest/parse_latex.py", "scripts/ingest/parse_docx.py", "scripts/journals/match_journals.py", "scripts/render/render_latex.py", "scripts/validate/check_citations.py"]:
        body = text(rel)
        this_ok = "load_flat_module" in body or "_validation_cli" in body or "_compat" in body
        delegate_ok &= this_ok
        shim_hits.append(f"{rel}:{this_ok}")
    out.append(result("V2-F3", delegate_ok, "; ".join(shim_hits),
        "Parallel independent implementations drift and split fixes.",
        "Make subdirectory CLIs thin delegates to the canonical flat modules."))

    # V2-F4 — governance self-consistency is about reviewed changes, not required-path count.
    approved = set(manifest.get("approved_bugfix_paths", []))
    reasons = set((manifest.get("approved_bugfix_reasons") or {}).keys())
    ok = bool(approved) and approved <= reasons and manifest.get("policy", {}).get("baseline_file_changes_require_allowlist") is True
    out.append(result("V2-F4", ok, f"approved paths={len(approved)}; reasons cover all={approved <= reasons}",
        "An incoherent allowlist can either block legitimate maintenance or silently permit unexplained baseline edits.",
        "Require one review reason per approved baseline path; do not equate required existence paths with mutable allowlist."))

    # V2-F5 — S8 should be open-box from workdir and degrade honestly.
    formerly_required = ["--ir", "--bib", "--manuscript", "--journal-name", "--issn", "--aims-scope-file", "--scope-source-url"]
    manual_required = [flag for flag in formerly_required if f'ap.add_argument("{flag}", required=True' in rr]
    ok = not manual_required and 'ap.add_argument("--workdir", required=True' in rr and exists("scripts/readiness/pipeline_bridge.py")
    out.append(result("V2-F5", ok, f"manual required flags={manual_required}; pipeline_bridge={exists('scripts/readiness/pipeline_bridge.py')}",
        "A hand-fed readiness suite is not usable as part of the main workflow.",
        "Auto-resolve pipeline artifacts; keep official evidence missing as a blocker and document network degradation."))

    # V2-F6 — preservation wording and legacy sample must be explicitly non-security/compatibility.
    guard = text("scripts/check_preservation.py")
    ok = "not an anti-tamper" in guard and "COMPATIBILITY ALIAS" in alias
    out.append(result("V2-F6", ok, "regression guard disclaimer + labelled compatibility sample",
        "Security-like wording or unexplained duplicate samples create false confidence/confusion.",
        "Use compatibility-regression terminology and label the legacy example."))

    # V1-F4 — prompt inventory must include every actual prompt.
    prompt_files = []
    for p in (ROOT / "prompts").rglob("*.md"):
        if p.name == "README.md":
            continue
        prompt_files.append(str(p.relative_to(ROOT / "prompts")))
    missing_prompts = [p for p in prompt_files if Path(p).name not in prompt_readme]
    out.append(result("V1-F4", not missing_prompts, f"unlisted prompts={missing_prompts}",
        "Unlisted prompts become invisible/orphaned in maintenance and routing.",
        "Keep prompts/README.md inventory synchronized, including shared guidance files."))

    # V1-F5 — known architecture/troubleshooting references must resolve.
    ok = exists("docs/architecture.md") and exists("references/troubleshooting.md")
    out.append(result("V1-F5", ok, "docs/architecture.md and references/troubleshooting.md",
        "Dead links break the documented recovery path.",
        "Restore referenced docs or remove stale references."))

    # V1-F6 — extensions must be routed and capability boundaries explicit.
    normalized_router = router.replace("**", "").lower()
    ok = all(token in router for token in ("08-sci-writing.md", "09-language-polish.md", "10-submission-journal-search.md", "11-publication-readiness-orchestrator.md")) and "do not claim" in normalized_router
    out.append(result("V1-F6", ok, "extension router covers W/P/J/S8 and states truthfulness boundary",
        "Prompt-only features can be mistaken for deterministic executed checks.",
        "Route every extension and explicitly distinguish Agent-only from runtime checks."))

    # V1-F7 — extension governance is anchored to a prior commit and reviewed change list.
    ext_base = manifest.get("extension_baseline_commit")
    ext_approved = set(manifest.get("approved_extension_change_paths", []))
    ext_reasons = set((manifest.get("approved_extension_change_reasons") or {}).keys())
    ok = bool(ext_base) and ext_approved <= ext_reasons and "extension_baseline_commit" in text("scripts/check_preservation.py")
    out.append(result("V1-F7", ok, f"extension baseline={ext_base}; reviewed extension changes={len(ext_approved)}",
        "Presence-only extension checks allow safety/readiness behavior to weaken without a regression signal.",
        "Compare governed extension paths against a fixed prior commit and require reviewed reasons for changes."))

    # V1-F8 — real mode must be artifact-consumer, not a fake LLM toggle.
    ok = "real S2 artifact" in runner and "does not call an LLM" in runner and "--no-ai-stub" in runner
    out.append(result("V1-F8", ok, "--no-ai-stub explicitly consumes real Agent artifacts",
        "A misleading production toggle can crash downstream or imply nonexistent AI integration.",
        "Require pre-existing real Agent artifacts and document the boundary."))

    # V1-F9 — deliberate identifier mismatch must be documented, not silently changed.
    ok = "math-modeling-to-sci-skill" in readme and "math-modeling-to-sci`" in readme and "Skill 标识" in readme
    out.append(result("V1-F9", ok, "README documents repository/distribution name vs Skill identifier",
        "Unexplained name mismatch confuses installation and invocation.",
        "Document the intentional compatibility identifier; do not mutate the protected legacy frontmatter."))

    # V1-F10 — CHANGELOG concrete script paths must exist.
    bad_change = [("CHANGELOG.md", ref) for ref in SCRIPT_REF_RE.findall(changelog) if "..." not in ref and not exists(ref)]
    out.append(result("V1-F10", not bad_change, f"bad CHANGELOG script refs={bad_change}",
        "A changelog that names nonexistent architecture is misleading provenance.",
        "Correct historical paths and avoid claiming files/workflows that do not exist."))

    # V1-F11 — mixed shared naming is acceptable only with an explicit convention.
    ok = "shared 命名约定" in prompt_readme and "05-" in prompt_readme and "06-" in prompt_readme
    out.append(result("V1-F11", ok, "prompts/README.md documents legacy shared vs numbered additive policies",
        "Undocumented mixed naming looks accidental and encourages inconsistent additions.",
        "Document the compatibility naming convention rather than renaming referenced legacy files."))

    # V1-F12 — CI must exist and run pytest + this audit.
    ci = text(".github/workflows/ci.yml")
    ok = exists(".github/workflows/ci.yml") and exists(".github/workflows/validate-skill.yml") and "pytest" in ci and "audit_repo.py" in ci
    out.append(result("V1-F12", ok, "ci.yml + validate-skill.yml; CI runs pytest and audit_repo.py",
        "Without CI, regressions can merge unnoticed.",
        "Run static audit, preservation guard and pytest on pull requests."))

    return out


def main() -> int:
    results = audit()
    failed = [r for r in results if r["status"] != "PASS"]
    print("REPOSITORY RISK AUDIT")
    for r in results:
        marker = "✅" if r["status"] == "PASS" else "❌"
        print(f"{marker} {r['risk']} {r['status']} — {r['evidence']}")
        if r["status"] != "PASS":
            print(f"   impact: {r['impact']}")
            print(f"   fix: {r['fix']}")
    print(f"SUMMARY: pass={len(results)-len(failed)} fail={len(failed)} total={len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
