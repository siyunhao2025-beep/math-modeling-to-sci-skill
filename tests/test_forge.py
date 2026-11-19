from __future__ import annotations

import importlib.util
import json
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


def verification(required="source_bound", reached=None, locator="R1") -> dict:
    return {
        "required_depth": required,
        "reached_depth": reached or required,
        "checked_at": "2026-11-14T10:00:00+08:00",
        "evidence_locator": locator,
    }


def citation(**overrides) -> dict:
    row = {
        "citation_id": "R1",
        "identity_status": "VERIFIED",
        "integrity_status": "NO_SIGNAL_FOUND",
        "integrity_checked_at": "2026-11-18T10:00:00+08:00",
        "integrity_source_url": "https://publisher.example/article/R1",
        "correction_effect": "NOT_APPLICABLE",
        "support_status": "SUPPORTS",
        "sentence_tier": "background",
        "access_level": "metadata_only",
        "locator": "",
    }
    row.update(overrides)
    return row


def g_workspace_with_citation(tmp_path: Path, row: dict) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    work = init_workspace(tmp_path)
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The cited work establishes the background.",
            "evidence_ids": ["R1"], "risk": "low", "status": "SUPPORTED",
            "verification": verification(),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True, "figures": [], "waiver_reason": "No figure is needed for this claim."
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [], "citations": [row],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")
    return work


def g_workspace_with_figure(tmp_path: Path, editable_artifact: dict) -> Path:
    work = init_workspace(tmp_path)
    output = work / "04-manuscript" / "fig-method.svg"
    output.write_text("<svg/>", encoding="utf-8")
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The workflow preserves traceability.",
            "evidence_ids": ["R1"], "risk": "low", "status": "SUPPORTED",
            "verification": verification(),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "figure_type": "schematic", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "editable_artifact": editable_artifact,
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig-method.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-11-19T10:00:00+08:00",
                "reviewed_width_mm": 85.0,
                "output_sha256": {"04-manuscript/fig-method.svg": forge.sha256(output)},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [], "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")
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
            "verification": verification(),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True, "figures": [], "waiver_reason": "The single claim is reported in a table."
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation(
            sentence_tier="quantitative", access_level="abstract_only", locator=""
        )],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")
    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("too shallow" in item for item in result["errors"])
    assert any("locator" in item for item in result["errors"])


def test_g_gate_requires_publication_integrity_as_a_separate_axis(tmp_path):
    row = citation()
    for field in (
        "integrity_status", "integrity_checked_at", "integrity_source_url", "correction_effect"
    ):
        row.pop(field)
    result = forge.evaluate(g_workspace_with_citation(tmp_path, row), "G")
    assert not result["passed"]
    assert any("integrity_status" in item for item in result["errors"])


def test_g_gate_blocks_fatal_or_unresolved_integrity_signals(tmp_path):
    for status in (
        "RETRACTED", "WITHDRAWN", "REMOVED", "EXPRESSION_OF_CONCERN", "NOT_CHECKED"
    ):
        row = citation(integrity_status=status)
        if status == "NOT_CHECKED":
            row.update(integrity_checked_at="", integrity_source_url="")
        result = forge.evaluate(g_workspace_with_citation(tmp_path / status.lower(), row), "G")
        assert not result["passed"], status
        assert any(status in item for item in result["errors"]), result


def test_g_gate_requires_correction_effect_and_locator(tmp_path):
    for effect in ("UNKNOWN", "AFFECTS_CITED_CONTENT"):
        result = forge.evaluate(g_workspace_with_citation(
            tmp_path / effect.lower(),
            citation(
                integrity_status="CORRECTED",
                correction_effect=effect,
                correction_locator="https://publisher.example/correction/R1",
            ),
        ), "G")
        assert not result["passed"], effect
        assert any(effect in item for item in result["errors"]), result

    result = forge.evaluate(g_workspace_with_citation(
        tmp_path / "missing-locator",
        citation(integrity_status="CORRECTED", correction_effect="UNAFFECTED"),
    ), "G")
    assert not result["passed"]
    assert any("correction_locator" in item for item in result["errors"])


def test_g_gate_accepts_checked_record_and_unaffected_correction(tmp_path):
    clean = forge.evaluate(g_workspace_with_citation(
        tmp_path / "no-signal", citation()
    ), "G")
    assert clean["passed"], clean

    corrected = forge.evaluate(g_workspace_with_citation(
        tmp_path / "corrected",
        citation(
            integrity_status="CORRECTED",
            correction_effect="UNAFFECTED",
            correction_locator="https://publisher.example/correction/R1",
        ),
    ), "G")
    assert corrected["passed"], corrected


def test_g_gate_rejects_untraceable_integrity_check(tmp_path):
    row = citation(
        integrity_checked_at="2026-11-18T10:00:00",
        integrity_source_url="http://publisher.example/article/R1",
    )
    result = forge.evaluate(g_workspace_with_citation(tmp_path, row), "G")
    assert not result["passed"]
    assert any("timezone-aware" in item for item in result["errors"])
    assert any("HTTPS" in item for item in result["errors"])


def test_g_gate_rejects_visual_review_after_reviewed_output_changes(tmp_path):
    work = init_workspace(tmp_path)
    figure = work / "04-manuscript" / "fig1.svg"
    figure.write_text("reviewed version", encoding="utf-8")
    reviewed_hash = forge.sha256(figure)
    figure.write_text("changed after review", encoding="utf-8")

    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The validated model reproduces the reference case.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
            "verification": verification("execution_bound", locator="03-revalidation/run-log.json#R1"),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig1.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-10-18T12:00:00Z",
                "reviewed_width_mm": 85.0,
                "output_sha256": {"04-manuscript/fig1.svg": reviewed_hash},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("changed after visual review" in item for item in result["errors"])


def test_g_gate_accepts_visual_review_bound_to_current_outputs(tmp_path):
    work = init_workspace(tmp_path)
    figure = work / "04-manuscript" / "fig1.svg"
    figure.write_text("reviewed version", encoding="utf-8")
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The validated model reproduces the reference case.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
            "verification": verification("execution_bound", locator="03-revalidation/run-log.json#R1"),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig1.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-10-18T12:00:00Z",
                "reviewed_width_mm": 85.0,
                "output_sha256": {"04-manuscript/fig1.svg": forge.sha256(figure)},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")

    result = forge.evaluate(work, "G")
    assert result["passed"], result


def test_g_gate_accepts_editable_schematic_with_stable_object_ids(tmp_path):
    work = g_workspace_with_figure(tmp_path, {
        "source": "04-manuscript/fig-method.svg", "format": "svg",
        "objects": [
            {"object_id": "input", "kind": "node"},
            {"object_id": "model", "kind": "node"},
            {"object_id": "input-to-model", "kind": "connector",
             "source_id": "input", "target_id": "model"},
        ],
    })

    result = forge.evaluate(work, "G")
    assert result["passed"], result


def test_g_gate_rejects_duplicate_or_dangling_semantic_objects(tmp_path):
    work = g_workspace_with_figure(tmp_path, {
        "source": "04-manuscript/fig-method.svg", "format": "svg",
        "objects": [
            {"object_id": "input", "kind": "node"},
            {"object_id": "input", "kind": "node"},
            {"object_id": "edge", "kind": "connector",
             "source_id": "input", "target_id": "missing"},
        ],
    })

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("duplicate semantic object IDs" in item for item in result["errors"])
    assert any("unknown target_id" in item for item in result["errors"])


def test_g_gate_rejects_supported_claim_without_verification_depth(tmp_path):
    work = init_workspace(tmp_path)
    figure = work / "04-manuscript" / "fig1.svg"
    figure.write_text("reviewed version", encoding="utf-8")
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The validated model reproduces the reference case.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig1.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-11-14T10:00:00+08:00",
                "reviewed_width_mm": 85.0,
                "output_sha256": {"04-manuscript/fig1.svg": forge.sha256(figure)},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("verification" in item and "required_depth" in item
               for item in result["errors"])


def test_g_gate_rejects_shallow_or_under_reached_verification(tmp_path):
    work = init_workspace(tmp_path)
    figure = work / "04-manuscript" / "fig1.svg"
    figure.write_text("reviewed version", encoding="utf-8")
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The validated model reproduces the reference case.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
            "verification": verification(
                "execution_bound", reached="source_bound", locator="03-revalidation/run-log.json#R1"
            ),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig1.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-11-14T10:00:00+08:00",
                "reviewed_width_mm": 85.0,
                "output_sha256": {"04-manuscript/fig1.svg": forge.sha256(figure)},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("below required_depth" in item for item in result["errors"])

    claim_map = json.loads((work / "04-manuscript" / "claim-map.json").read_text(encoding="utf-8"))
    claim_map["claims"][0]["verification"] = verification(
        "text_bound", reached="text_bound", locator="04-manuscript/manuscript.md#results"
    )
    dump(work / "04-manuscript" / "claim-map.json", claim_map)

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("Gate G minimum 'source_bound'" in item for item in result["errors"])


def test_g_gate_rejects_visual_review_at_wrong_final_width(tmp_path):
    work = init_workspace(tmp_path)
    figure = work / "04-manuscript" / "fig1.svg"
    figure.write_text("reviewed version", encoding="utf-8")
    dump(work / "04-manuscript" / "claim-map.json", {
        "complete": True,
        "claims": [{
            "claim_id": "C1", "text": "The validated model reproduces the reference case.",
            "evidence_ids": ["R1"], "risk": "high", "status": "SUPPORTED",
            "verification": verification("execution_bound", locator="03-revalidation/run-log.json#R1"),
        }],
    })
    dump(work / "04-manuscript" / "figure-manifest.json", {
        "complete": True,
        "figures": [{
            "figure_id": "F1", "claim_ids": ["C1"],
            "source_data": ["03-revalidation/validation-results.json"],
            "target_width_mm": 85.0,
            "outputs": ["04-manuscript/fig1.svg"],
            "visual_review": {
                "reviewer": "author", "reviewed_at": "2026-10-22T12:00:00Z",
                "reviewed_width_mm": 178.0,
                "output_sha256": {"04-manuscript/fig1.svg": forge.sha256(figure)},
            },
        }],
    })
    dump(work / "04-manuscript" / "citation-audit.json", {
        "complete": True, "blockers": [],
        "citations": [citation()],
    })
    (work / "04-manuscript" / "manuscript.md").write_text("draft", encoding="utf-8")

    result = forge.evaluate(work, "G")
    assert not result["passed"]
    assert any("reviewed_width_mm" in item and "target_width_mm" in item
               for item in result["errors"])
