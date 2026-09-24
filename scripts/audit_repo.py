#!/usr/bin/env python3
"""Offline repository audit for the reviewed FORGE v2 distribution.

PASS means the named packaging or regression property is present. It does not
certify scientific validity, journal acceptance, or live external evidence.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REF_RE = re.compile(r"(?<![\w.-])(scripts/[A-Za-z0-9_./-]+\.py)")
REF_RE = re.compile(r"`(references/[A-Za-z0-9_./-]+\.md)`")


def text(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def result(risk: str, ok: bool, evidence: str, impact: str, fix: str = "") -> dict:
    return {
        "risk": risk,
        "status": "PASS" if ok else "FAIL",
        "evidence": evidence,
        "impact": impact,
        "fix": fix if not ok else "-",
    }


def frontmatter_keys(body: str) -> list[str]:
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    try:
        end = lines.index("---", 1)
    except ValueError:
        return []
    return [m.group(1) for line in lines[1:end]
            if (m := re.match(r"^([A-Za-z0-9_-]+):", line))]


def markdown_script_refs() -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", "runs", ".pytest_cache"} for part in path.parts):
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for ref in SCRIPT_REF_RE.findall(body):
            if "..." not in ref:
                refs.append((path.relative_to(ROOT).as_posix(), ref))
    return refs


def preservation_errors() -> list[str]:
    path = ROOT / "scripts" / "check_preservation.py"
    spec = importlib.util.spec_from_file_location("forge_preservation_check", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    errors, _ = module.verify(ROOT, ROOT / "config" / "preservation-manifest.json")
    return errors


def audit() -> list[dict]:
    out: list[dict] = []
    skill = text("SKILL.md")
    readme = text("README.md")
    runner = text("scripts/run_pipeline.py")
    bridge = text("scripts/readiness/pipeline_bridge.py")
    provenance = text("references/provenance.md")

    keys = frontmatter_keys(skill)
    out.append(result("F2-01", keys == ["name", "description"], f"frontmatter keys={keys}",
                      "Extra metadata can make the skill invalid for current loaders.",
                      "Keep only name and description in SKILL.md frontmatter."))

    lines = len(skill.splitlines())
    out.append(result("F2-02", 0 < lines < 500, f"SKILL.md lines={lines}",
                      "An oversized entry point consumes context and hides routing.",
                      "Move detailed rules into directly linked references."))

    refs = sorted(set(REF_RE.findall(skill)))
    missing_refs = [rel for rel in refs if not exists(rel)]
    out.append(result("F2-03", len(refs) >= 8 and not missing_refs,
                      f"linked references={len(refs)} missing={missing_refs}",
                      "Broken progressive-disclosure links make routes unusable.",
                      "Restore every reference linked by SKILL.md."))

    agent = text("agents/openai.yaml")
    ok = all(x in agent for x in ("display_name:", "short_description:",
                                   "default_prompt:", "$math-modeling-to-sci"))
    out.append(result("F2-04", ok, "agents/openai.yaml UI metadata and explicit default invocation",
                      "Stale UI metadata weakens discovery and launches the wrong task.",
                      "Regenerate agents/openai.yaml from SKILL.md."))

    hero = ROOT / "assets" / "brand" / "m2sci-forge-hero.png"
    ok = hero.is_file() and hero.stat().st_size > 100_000 and "assets/brand/m2sci-forge-hero.png" in readme
    out.append(result("F2-05", ok, f"hero exists={hero.is_file()} bytes={hero.stat().st_size if hero.is_file() else 0}",
                      "A missing or placeholder hero breaks the requested launch presentation.",
                      "Restore the final brand artwork and README link."))

    slogan = "不把建模报告翻译成英文；把模型证据锻造成经得起审稿的 SCI 论文。"
    out.append(result("F2-06", slogan in skill and slogan in readme, "brand slogan synchronized",
                      "Inconsistent positioning makes the skill look like generic polishing.",
                      "Use the approved slogan in both entry point and README."))

    ok = all(exists(x) for x in ("scripts/forge.py", "config/forge-trace.yaml",
                                  "config/schema/forge-project.schema.json"))
    out.append(result("F2-07", ok, "FORGE CLI, config and project schema present",
                      "The named framework would otherwise be documentation-only.",
                      "Restore the deterministic FORGE contract layer."))

    forge_body = text("scripts/forge.py")
    ok = all(f'add_parser("{name}"' in forge_body for name in ("init", "status", "gate", "impact"))
    out.append(result("F2-08", ok, "FORGE CLI exposes init/status/gate/impact",
                      "Missing commands break the advertised lifecycle.",
                      "Implement and test every documented FORGE command."))

    out.append(result("F2-09", exists("tests/test_forge.py") and "test_impact" in text("tests/test_forge.py"),
                      "FORGE gate and impact regression tests present",
                      "Untested gates can silently promote incomplete artifacts.",
                      "Add contract, blocker and propagation tests."))

    orphan_bridges = [
        path for path in ("scripts/corpus.py", "scripts/research.py", "scripts/upstream.py")
        if exists(path)
    ]
    ok = not exists("research-mother") and not orphan_bridges
    out.append(result("F2-10", ok,
                      f"no nested Research Mother copy or orphan bridges={orphan_bridges}",
                      "Vendoring a second skill or retaining bridges to removed code creates conflicting rules and broken entry points.",
                      "Keep attributed principles, not a nested repository or dead compatibility scripts."))

    ok = all(exists(x) for x in ("scripts/run_pipeline.py", "scripts/gates.py",
                                  "scripts/readiness/run_readiness.py"))
    out.append(result("F2-11", ok, "legacy S1-S8 compatibility runtime retained",
                      "A clean redesign must not discard proven parsing/readiness utilities.",
                      "Restore the compatibility runtime or document a migration."))

    ok = all(x in runner for x in ("run_readiness_from_workdir", "--readiness", "[S8]"))
    out.append(result("F2-12", ok, "S8 remains reachable from run_pipeline.py",
                      "Publication readiness would become an orphan feature.",
                      "Keep the S8 bridge wired before final reporting."))

    risky_glyphs = tuple(chr(codepoint) for codepoint in (0x2705, 0x26D4, 0x274C))
    bad_console = [x for x in risky_glyphs if x in runner]
    out.append(result("F2-13", not bad_console, f"unsafe console glyphs={bad_console}",
                      "Legacy Windows consoles can crash on unencodable status glyphs.",
                      "Use ASCII status markers in command-line output."))

    ok = "def _portable" in bridge and ".as_posix()" in bridge
    out.append(result("F2-14", ok, "readiness bridge serializes portable paths",
                      "OS-specific separators break tests and exchanged artifacts.",
                      "Serialize resolved paths with forward slashes."))

    errors = preservation_errors()
    out.append(result("F2-15", not errors, f"distribution contract errors={errors}",
                      "Missing reviewed entry points or capability files create incomplete releases.",
                      "Update required paths and the reviewed SKILL contract together."))

    bad_refs = [(src, ref) for src, ref in markdown_script_refs() if not exists(ref)]
    out.append(result("F2-16", not bad_refs, f"missing documented scripts={bad_refs[:10]}",
                      "Copy-paste commands would fail.",
                      "Fix the documented path or restore the real script."))

    statuses = ("NOT_READY_FOR_CONVERSION", "BLOCKED", "AUTHOR_ACTION_REQUIRED",
                "READY_FOR_HUMAN_SUBMISSION_CHECK")
    ok = all(x in skill and x in readme for x in statuses)
    out.append(result("F2-17", ok, "four conservative top-level statuses synchronized",
                      "Unbounded success labels invite false submission-readiness claims.",
                      "Keep the four reviewed statuses in both user and agent docs."))

    commits = ("3d044caf26d602ba08eddc93397b3923397b82bc",
               "a6804fc85bc7336a3b418bf4ba29d0e3956159ed",
               "ecee288b4458c328236790111b5fa7c875383de7")
    ok = all(x in provenance for x in commits) and "MIT" in text("LICENSE") and text("VERSION").strip() == "2.0.0"
    out.append(result("F2-18", ok, "three audited source commits, MIT license and VERSION=2.0.0",
                      "Missing provenance or versioning obscures what was actually integrated.",
                      "Record audited commits, license boundaries and release version."))

    nested_required = (
        "skills/scientific-figure-making/SKILL.md",
        "skills/scientific-figure-making/LICENSE",
        "skills/scientific-figure-making/SOURCE.md",
        "skills/scientific-figure-making/agents/openai.yaml",
        "skills/scientific-figure-making/references/api.md",
        "skills/scientific-figure-making/references/common-patterns.md",
        "skills/scientific-figure-making/references/demos.md",
        "skills/scientific-figure-making/references/design-theory.md",
        "skills/scientific-figure-making/references/tutorials.md",
    )
    nested_skill = text("skills/scientific-figure-making/SKILL.md")
    nested_source = text("skills/scientific-figure-making/SOURCE.md")
    nested_demos = text("skills/scientific-figure-making/references/demos.md")
    nested_agent = text("skills/scientific-figure-making/agents/openai.yaml")
    locked_commit = "3c181f85e82c6f24948fcaaf3be6696102b41d8d"
    ok = (
        all(exists(path) for path in nested_required)
        and frontmatter_keys(nested_skill) == ["name", "description"]
        and "../../references/figure-contract.md" in nested_skill
        and "../../references/figures4papers-profile.md" in nested_skill
        and "overrides every conflicting recommendation" in nested_skill
        and "$scientific-figure-making" in nested_agent
        and "not relicensed" in nested_source
        and locked_commit in nested_source
        and f"/tree/{locked_commit}/" in nested_demos
        and "/tree/main/" not in nested_demos
    )
    out.append(result("F2-19", ok,
                      "vendored scientific-figure-making skill, local safety precedence, pinned demos and CC BY-NC boundary",
                      "A partial or ungoverned nested skill could bypass evidence gates or be misrepresented as MIT.",
                      "Restore the complete nested skill and its license/source/safety contract."))
    return out


def main() -> int:
    results = audit()
    failed = [item for item in results if item["status"] != "PASS"]
    print("FORGE V2 REPOSITORY AUDIT")
    for item in results:
        marker = "[OK]" if item["status"] == "PASS" else "[FAIL]"
        print(f"{marker} {item['risk']} {item['status']} - {item['evidence']}")
        if item["status"] != "PASS":
            print(f"   impact: {item['impact']}")
            print(f"   fix: {item['fix']}")
    print(f"SUMMARY: pass={len(results) - len(failed)} fail={len(failed)} total={len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
