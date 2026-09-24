from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "scientific-figure-making"
LOCKED_COMMIT = "3c181f85e82c6f24948fcaaf3be6696102b41d8d"
EXPECTED_FILES = {
    "SKILL.md",
    "LICENSE",
    "SOURCE.md",
    "agents/openai.yaml",
    "references/api.md",
    "references/common-patterns.md",
    "references/demos.md",
    "references/design-theory.md",
    "references/tutorials.md",
}


def _text(relative: str) -> str:
    return (SKILL_DIR / relative).read_text(encoding="utf-8")


def _normalized_sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def test_vendored_skill_has_the_complete_documentation_package():
    actual = {
        path.relative_to(SKILL_DIR).as_posix()
        for path in SKILL_DIR.rglob("*")
        if path.is_file()
    }
    assert actual == EXPECTED_FILES
    assert _text("SKILL.md").startswith("---\nname: scientific-figure-making\n")
    for name in (
        "api.md",
        "common-patterns.md",
        "demos.md",
        "design-theory.md",
        "tutorials.md",
    ):
        assert (SKILL_DIR / "references" / name).is_file()


def test_skill_is_independently_discoverable():
    skill = _text("SKILL.md")
    frontmatter = skill.split("---", 2)[1]
    keys = re.findall(r"^([A-Za-z0-9_-]+):", frontmatter, flags=re.MULTILINE)
    assert keys == ["name", "description"]

    agent = _text("agents/openai.yaml")
    assert 'display_name: "Scientific Figure Making"' in agent
    assert 'short_description: "Evidence-first publication figures in Matplotlib"' in agent
    assert "$scientific-figure-making" in agent
    assert "allow_implicit_invocation: true" in agent


def test_repository_contract_overrides_unsafe_upstream_defaults():
    skill = _text("SKILL.md")
    for required in (
        "../../references/figure-contract.md",
        "../../references/figures4papers-profile.md",
        "../../references/model-validation-matrix.md",
        "../../references/forge-trace-framework.md",
        "Magnitude bars start at zero",
        "alpha-only",
        "red–green-only",
        "Fixed ultra-wide canvases are not a default",
        "overrides every conflicting recommendation",
    ):
        assert required in skill

    patterns = _text("references/common-patterns.md")
    assert "forbidden for magnitude bars" in patterns
    assert "do not copy these fixed sizes" in patterns
    assert "keeps every mark unambiguous" in patterns

    api = _text("references/api.md")
    assert "never use red–green or alpha alone" in api
    assert "magnitude bars use a zero baseline" in api

    tutorials = _text("references/tutorials.md")
    assert "ax.set_ylim(0, 1.0)" in tutorials
    assert "ax.set_ylim(0.7, 1.0)" not in tutorials


def test_demo_tree_links_are_pinned_and_main_is_not_a_target():
    demos = _text("references/demos.md")
    tree_urls = re.findall(r"https://github\.com/ChenLiu-1996/figures4papers/tree/[^)\s]+", demos)
    assert len(tree_urls) == 8
    assert all(f"/tree/{LOCKED_COMMIT}/" in url for url in tree_urls)
    assert not any("/tree/main/" in url for url in tree_urls)


def test_cc_by_nc_license_and_change_notice_are_preserved():
    assert _normalized_sha256(SKILL_DIR / "LICENSE") == (
        "0afca3145596cd005f6f6ed977313ea31928094fc5b4aaabc21bb765ea369d09"
    )
    source = _text("SOURCE.md")
    for required in (
        LOCKED_COMMIT,
        "CC BY-NC 4.0",
        "not relicensed",
        "Change indication",
        "Commercial reuse requires separate permission",
    ):
        assert required in source

    provenance = (ROOT / "references" / "provenance.md").read_text(encoding="utf-8")
    assert "不被仓库根 MIT License 重新许可" in provenance


def test_lock_and_preservation_manifest_register_every_nested_file():
    lock = json.loads((ROOT / "config" / "figures4papers.lock.json").read_text(encoding="utf-8"))
    vendored = lock["integration_policy"]["vendored_skill"]
    assert vendored["path"] == "skills/scientific-figure-making"
    assert vendored["license"] == "CC-BY-NC-4.0"
    assert vendored["relicensed_under_root_mit"] is False
    assert lock["integration_policy"]["bundled_upstream_code"] is False
    assert lock["integration_policy"]["bundled_upstream_images"] is False
    assert lock["integration_policy"]["bundled_upstream_pdfs"] is False

    manifest = json.loads(
        (ROOT / "config" / "preservation-manifest.json").read_text(encoding="utf-8")
    )
    registered = set(manifest["required_paths_without_git_history"])
    expected_registered = {
        f"skills/scientific-figure-making/{relative}" for relative in EXPECTED_FILES
    }
    assert expected_registered <= registered
    assert "tests/test_vendored_scientific_figure_skill.py" in registered
