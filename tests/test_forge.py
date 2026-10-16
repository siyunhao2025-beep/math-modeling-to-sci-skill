from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("forge_cli", ROOT / "scripts" / "forge.py")
forge = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(forge)


class Args:
    pass


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def init_workspace(tmp_path: Path) -> Path:
    source = tmp_path / "report.tex"
    source.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
    work = tmp_path / "run"
    args = Args()
    args.workspace = str(work)
    args.input = str(source)
    args.route = "full"
    assert forge.command_init(args) == 0
    return work


def complete_f(work: Path) -> None:
    dump(work / "01-forensics" / "asset-inventory.json", {
        "schema_version": "2.0",
        "complete": True,
        "assets": [
            {"id": "eq-1", "type": "equation", "source_locator": "report.tex:1"},
            {"id": "claim-1", "type": "conclusion", "source_locator": "report.tex:1"},
        ],
    })
    dump(work / "01-forensics" / "disposition-ledger.json", {
        "schema_version": "2.0",
        "complete": True,
        "entries": [
            {"asset_id": "eq-1", "action": "retain"},
            {"asset_id": "claim-1", "action": "adapt"},
        ],
    })


def test_init_creates_snapshot_but_does_not_fake_gate_pass(tmp_path):
    work = init_workspace(tmp_path)
    manifest = json.loads((work / "00-source" / "source-manifest.json").read_text(encoding="utf-8"))
    snap = work / manifest["files"][0]["snapshot_path"]
    assert snap.is_file()
    result = forge.evaluate(work, "F")
    assert not result["passed"]
    assert any("inventory" in item for item in result["errors"])


def test_f_gate_passes_complete_inventory_and_dispositions(tmp_path):
    work = init_workspace(tmp_path)
    complete_f(work)
    result = forge.evaluate(work, "F")
    assert result["passed"], result


def test_gate_command_advances_stale_pointer_in_order(tmp_path):
    work = init_workspace(tmp_path)
    complete_f(work)
    args = Args()
    args.workspace = str(work)
    args.phase = "F"
    assert forge.command_gate(args) == 0
    project = json.loads((work / "forge-project.json").read_text(encoding="utf-8"))
    assert project["stale_from"] == "O"
    args.phase = "R"
    assert forge.command_gate(args) == 2
    gate = json.loads((work / "audit" / "gate-r.json").read_text(encoding="utf-8"))
    assert any("phase O is stale" in item for item in gate["errors"])


def test_drop_requires_reason_and_author_approval(tmp_path):
    work = init_workspace(tmp_path)
    dump(work / "01-forensics" / "asset-inventory.json", {
        "complete": True,
        "assets": [{"id": "table-1", "type": "table", "source_locator": "report.tex:2"}],
    })
    dump(work / "01-forensics" / "disposition-ledger.json", {
        "complete": True,
        "entries": [{"asset_id": "table-1", "action": "drop"}],
    })
    result = forge.evaluate(work, "F")
    assert not result["passed"]
    assert any("author_approved" in item for item in result["errors"])


def test_o_gate_rejects_keyword_label_outside_archetypes(tmp_path):
    work = init_workspace(tmp_path)
    dump(work / "02-opportunity" / "research-positioning.json", {
        "complete": True,
        "problem": "P", "gap": "G", "approach": "A", "evidence": "E",
        "contribution": "C", "boundary": "B", "conversion_status": "eligible",
    })
    dump(work / "02-opportunity" / "model-profile.json", {
        "complete": True,
        "primary_archetype": "deep-learning-because-keywords",
        "secondary_archetypes": [], "assumptions": ["A1"], "risks": ["R1"],
    })
    result = forge.evaluate(work, "O")
    assert not result["passed"]
    assert any("primary_archetype" in item for item in result["errors"])


def test_high_risk_claim_needs_two_validation_routes(tmp_path):
    work = init_workspace(tmp_path)
    dump(work / "03-revalidation" / "validation-plan.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "risk": "high",
            "tests": [{"method": "baseline", "evidence_type": "comparison"}],
        }],
    })
    dump(work / "03-revalidation" / "validation-results.json", {
        "complete": True,
        "baseline_status": "compared", "baseline_reason": "",
        "runs": [{"run_id": "r1", "executed": True, "result_locator": "results/r1.csv"}],
        "unresolved_blockers": [],
    })
    result = forge.evaluate(work, "R")
    assert not result["passed"]
    assert any("at least 2" in item for item in result["errors"])


def test_impact_propagates_downstream_without_deleting_artifacts(tmp_path):
    work = init_workspace(tmp_path)
    sentinel = work / "04-manuscript" / "manuscript.md"
    sentinel.write_text("keep me", encoding="utf-8")
    args = Args()
    args.workspace = str(work)
    args.changed = ["03-revalidation/validation-results.json"]
    assert forge.command_impact(args) == 0
    report = json.loads((work / "audit" / "impact-report.json").read_text(encoding="utf-8"))
    assert report["earliest_affected_phase"] == "R"
    assert report["affected_phases"] == ["R", "G", "E"]
    assert sentinel.read_text(encoding="utf-8") == "keep me"


def test_e_gate_rejects_acceptance_probability(tmp_path):
    work = init_workspace(tmp_path)
    dump(work / "05-editorial" / "journal-evidence.json", {
        "complete": True,
        "selected_journal": "Journal A",
        "candidates": [{
            "name": "Journal A", "official_scope_url": "https://example.org/scope",
            "retrieved_at": "2026-09-22T00:00:00Z",
        }],
    })
    dump(work / "05-editorial" / "reviewer-panel.json", {
        "complete": True,
        "reviewers": [
            {"role": "editor"}, {"role": "domain"}, {"role": "methods"},
        ],
        "verdict": forge.READY,
        "acceptance_probability": 0.91,
    })
    dump(work / "05-editorial" / "submission-preflight.json", {
        "complete": True, "status": forge.READY, "blockers": [],
    })
    result = forge.evaluate(work, "E")
    assert not result["passed"]
    assert any("acceptance_probability" in item for item in result["errors"])


def test_g_gate_enforces_access_depth_for_quantitative_citation(tmp_path):
    work = init_workspace(tmp_path)
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The metric increased by 18%.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True, "figures": [], "waiver_reason": "The single claim is reported in a table."
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [{
            "citation_id": "R1", "identity_status": "VERIFIED",
            "support_status": "SUPPORTS", "sentence_tier": "quantitative",
            "access_level": "abstract_only", "locator": "",
        }],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")
    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("too shallow" in item for item in result["errors"])
    assert any("locator" in item for item in result["errors"])


def complete_g_with_locked_figure(work: Path) -> tuple[Path, Path, Path]:
    source = work / "03-revalidation" / "results" / "figure-1.csv"
    script = work / "04-manuscript" / "figures" / "plot_figure_1.py"
    output = work / "04-manuscript" / "figures" / "figure-1.svg"
    source.parent.mkdir(parents=True, exist_ok=True)
    script.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("x,y\n1,2\n", encoding="utf-8")
    script.write_text("# deterministic plotting source\n", encoding="utf-8")
    output.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>\n", encoding="utf-8")

    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The observed result is shown in Figure 1.",
            "evidence_ids": ["R1"], "risk": "low", "status": "SUPPORTED",
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "schema_version": "2.1",
        "complete": True,
        "waiver_reason": "",
        "figures": [{
            "figure_id": "F1",
            "claim_ids": ["C1"],
            "source_data": ["03-revalidation/results/figure-1.csv"],
            "script": "04-manuscript/figures/plot_figure_1.py",
            "outputs": ["04-manuscript/figures/figure-1.svg"],
            "sha256": {
                "source_data": {
                    "03-revalidation/results/figure-1.csv": forge.sha256(source),
                },
                "script": forge.sha256(script),
                "outputs": {
                    "04-manuscript/figures/figure-1.svg": forge.sha256(output),
                },
            },
            "final_size": {
                "slot_class": "single-column",
                "width_mm": 85.0,
                "height_mm": 60.0,
            },
            "editability": {
                "class": "live-vector-text",
                "notes": "Text and vector marks remain editable.",
            },
            "visual_review": {
                "reviewer": "Author",
                "reviewed_at": "2026-10-15T00:00:00Z",
                "at_width_mm": 85.0,
                "at_height_mm": 60.0,
                "container": "manuscript single-column slot",
                "editability_checked": True,
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True,
        "blockers": [],
        "citations": [{
            "citation_id": "R1",
            "identity_status": "VERIFIED",
            "support_status": "SUPPORTS",
            "sentence_tier": "background",
            "access_level": "metadata_only",
        }],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")
    return source, script, output


def test_g_gate_accepts_locked_figure_reviewed_at_final_size(tmp_path):
    work = init_workspace(tmp_path)
    complete_g_with_locked_figure(work)
    result = forge.evaluate(work, "G")
    assert result["passed"], result


def test_g_gate_rejects_stale_figure_after_source_change(tmp_path):
    work = init_workspace(tmp_path)
    source, _, _ = complete_g_with_locked_figure(work)
    source.write_text("x,y\n1,3\n", encoding="utf-8")
    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("source_data hash mismatch" in item for item in result["errors"])


def test_g_gate_rejects_output_that_is_the_source_file(tmp_path):
    work = init_workspace(tmp_path)
    source, _, _ = complete_g_with_locked_figure(work)
    path = work / "04-manuscript" / "figure-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    figure = manifest["figures"][0]
    source_rel = figure["source_data"][0]
    figure["outputs"] = [source_rel]
    figure["sha256"]["outputs"] = {source_rel: forge.sha256(source)}
    dump(path, manifest)

    result = forge.evaluate(work, "G")

    assert not result["passed"]
    assert any("aliases input source_data" in item for item in result["errors"]), result


def test_g_gate_rejects_output_hardlink_alias_of_script(tmp_path):
    work = init_workspace(tmp_path)
    _, script, output = complete_g_with_locked_figure(work)
    output.unlink()
    os.link(script, output)
    path = work / "04-manuscript" / "figure-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    output_rel = manifest["figures"][0]["outputs"][0]
    manifest["figures"][0]["sha256"]["outputs"][output_rel] = forge.sha256(output)
    dump(path, manifest)

    result = forge.evaluate(work, "G")

    assert not result["passed"]
    assert any("aliases input script" in item for item in result["errors"]), result


def test_g_gate_rejects_unreviewed_final_size_and_unknown_editability(tmp_path):
    work = init_workspace(tmp_path)
    complete_g_with_locked_figure(work)
    path = work / "04-manuscript" / "figure-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    figure = manifest["figures"][0]
    figure["editability"]["class"] = "fully-editable-somehow"
    figure["visual_review"]["at_width_mm"] = 170.0
    dump(path, manifest)
    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("editability.class" in item for item in result["errors"])
    assert any("final width" in item for item in result["errors"])
