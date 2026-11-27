from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from readiness.claim_evidence import run as claim_run  # noqa: E402
from readiness.compliance_audit import run as compliance_run  # noqa: E402
from readiness.figure_table_audit import run as figure_run  # noqa: E402
from readiness.reference_verifier import normalize_doi, source_coverage, verify_entry  # noqa: E402
from readiness.submission_preflight import run as preflight_run  # noqa: E402
from render import render_figures  # noqa: E402


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def clear_required_artifacts(wd: Path):
    dump(wd / "06-validate/validation-final.json", {
        "summary": {"error_count": 0, "unresolved_error_ids": []},
        "checkers": [],
    })
    dump(wd / "08-readiness/reference-verification.json", {"blockers": []})
    dump(wd / "08-readiness/citation-support-audit.json", {"citations": [], "blockers": []})
    dump(wd / "08-readiness/journal-fit.json", {
        "blockers": [],
        "baseline_fit_score_0_100": 90,
        "agent_semantic_review": {"decision": "STRONG_FIT"},
    })
    dump(wd / "08-readiness/claim-evidence-audit.json", {"blockers": [], "claims": []})
    dump(wd / "08-readiness/figure-table-audit.json", {"blockers": [], "visual_scientific_review": "PASS"})
    dump(wd / "08-readiness/compliance-audit.json", {"blockers": [], "recommended_reporting_guidelines": []})
    dump(wd / "08-readiness/reviewer-simulation.json", {"comments": [
        {"id": "RS-1", "severity": "major", "status": "RESOLVED"},
        {"id": "RS-2", "severity": "major", "status": "RESOLVED"},
        {"id": "RS-3", "severity": "minor", "status": "RESOLVED"},
    ]})


def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.1234/ABC.5") == "10.1234/ABC.5"
    assert normalize_doi("doi: 10.1000/xyz123.") == "10.1000/xyz123"
    assert normalize_doi(None) is None


def test_reference_source_coverage_separates_success_zero_hits_failure_and_skip():
    coverage = source_coverage([
        {"provider": "crossref", "found": True},
        {"provider": "semantic_scholar", "found": False, "status": 404},
        {"provider": "pubmed", "found": False, "status": None,
         "raw_error": {"error": "timeout"}},
    ])
    assert coverage["planned"] == ["crossref", "semantic_scholar", "pubmed"]
    assert coverage["attempted"] == ["crossref", "semantic_scholar", "pubmed"]
    assert coverage["succeeded"] == ["crossref"]
    assert coverage["zero_hits"] == ["semantic_scholar"]
    assert coverage["failed"] == [{"provider": "pubmed", "reason": "timeout"}]
    assert coverage["skipped"] == []
    assert coverage["exhaustiveness_claim_allowed"] is False

    skipped = source_coverage([], skip_reason="no DOI present")
    assert skipped["attempted"] == []
    assert [row["provider"] for row in skipped["skipped"]] == [
        "crossref", "semantic_scholar", "pubmed"
    ]
    unresolved = verify_entry({"ID": "fixture-without-doi", "title": "Synthetic title"})
    assert unresolved["status"] == "unverified"
    assert unresolved["source_coverage"]["outcome_counts"]["skipped"] == 3


def test_claim_evidence_blocks_unsupported_causal_claim(tmp_path):
    ir = {
        "meta": {"title": "x", "abstract": ""},
        "sections": [{
            "id": "sec-1",
            "semantic_role": "discussion",
            "blocks": [{"type": "paragraph", "text": "The forcing causes a 20% increase in temperature."}],
        }],
    }
    inp = tmp_path / "ir.json"
    out = tmp_path / "claim.json"
    dump(inp, ir)
    result = claim_run(str(inp), str(out))
    assert result["summary"]["claims_reviewed"] == 1
    assert result["blockers"] == ["claim-1"]


def test_s5_figure_shell_blocks_readiness_without_rewriting_build(tmp_path):
    figure = {"id": "F1", "path": "figure.pdf", "caption": "Model results under fixed conditions",
              "referenced_in": ["results"]}
    ir = tmp_path / "manuscript.ir.json"
    build = tmp_path / "main.tex"
    out = tmp_path / "08-readiness/figure-table-audit.json"
    dump(ir, {"figures": [figure]})
    (tmp_path / figure["path"]).touch()
    original = render_figures([figure])
    build.write_text(original, encoding="utf-8")

    result = figure_run(str(ir), str(out), str(build), str(tmp_path))
    assert [(x["code"], x["object"]) for x in result["blockers"]] == [
        ("BUILD_FIGURE_PLACEHOLDER", "F1"),
    ]
    assert result["visual_scientific_review"] == "PENDING_AGENT_REVIEW"
    assert build.read_text(encoding="utf-8") == original

    # A custom graphic can leave the S5 source comment in place.
    build.write_text(original.replace(r"\caption", "\\customplot\n  \\caption"), encoding="utf-8")
    assert not figure_run(str(ir), str(out), str(build), str(tmp_path))["blockers"]


def test_compliance_flags_missing_human_ethics(tmp_path):
    text = "We recruited 40 patients and evaluated the treatment. Data availability is described. Funding: none. Conflict of interest: none."
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")
    result = compliance_run(str(inp), str(out))
    assert "E01" in result["blockers"]
    assert "E02" in result["blockers"]


def test_compliance_blocks_vague_request_only_data_statement(tmp_path):
    text = (
        "Data availability. The data are available from the corresponding author "
        "upon reasonable request. Funding: none. Conflict of interest: none."
    )
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")

    result = compliance_run(str(inp), str(out))

    assert "E03" in result["blockers"]
    assert result["availability_statement_audit"]["data"]["status"] == "VAGUE_REQUEST_ONLY"


def test_compliance_accepts_located_public_data_but_requires_live_access_check(tmp_path):
    text = (
        "Data availability. The supporting data are deposited under the synthetic "
        "test identifier doi:10.0000/example.synthetic. Funding: none. "
        "Conflict of interest: none."
    )
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")

    result = compliance_run(str(inp), str(out))
    data = result["availability_statement_audit"]["data"]

    assert "E03" not in result["blockers"]
    assert data["status"] == "PUBLIC_WITH_LOCATOR"
    assert data["persistent_identifier_present"] is True
    assert data["logged_out_access_check"] == "REQUIRED_AT_SUBMISSION"


def test_compliance_requires_reason_and_route_for_restricted_data(tmp_path):
    text = (
        "Data availability. Participant-level data cannot be public because of "
        "confidentiality. Apply through https://access.example.invalid/form; "
        "applications are reviewed under a data use agreement. "
        "Funding: none. Conflict of interest: none."
    )
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")

    result = compliance_run(str(inp), str(out))
    data = result["availability_statement_audit"]["data"]

    assert "E03" not in result["blockers"]
    assert data["status"] == "RESTRICTED_WITH_REASON_AND_ROUTE"
    assert data["restriction_reason_present"] is True
    assert data["access_route_present"] is True


def test_compliance_flags_unlocated_code_repository_when_code_is_material(tmp_path):
    text = (
        "We implemented the simulation in Python. Code availability. Analysis code "
        "is available in a repository. Data are included in the supplementary "
        "material. Funding: none. Conflict of interest: none."
    )
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")

    result = compliance_run(str(inp), str(out))

    assert "R02" in result["warnings"]
    assert result["availability_statement_audit"]["code"]["status"] == "PRESENT_WITHOUT_ROUTE"


def test_compliance_accepts_combined_data_and_code_statement_for_both_subjects(tmp_path):
    text = (
        "We implemented the analysis in Python. Data and source code are available at "
        "https://example.invalid/archive/v1. Funding: none. Conflict of interest: none."
    )
    inp = tmp_path / "paper.txt"
    out = tmp_path / "compliance.json"
    inp.write_text(text, encoding="utf-8")

    result = compliance_run(str(inp), str(out))

    assert "E03" not in result["blockers"]
    assert "R02" not in result["warnings"]
    assert result["availability_statement_audit"]["data"]["status"] == "PUBLIC_WITH_LOCATOR"
    assert result["availability_statement_audit"]["code"]["status"] == "PUBLIC_WITH_LOCATOR"


def test_preflight_can_reach_human_check_when_all_required_artifacts_clear(tmp_path):
    wd = tmp_path / "run"
    clear_required_artifacts(wd)
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    assert result["status"] == "READY_FOR_HUMAN_SUBMISSION_CHECK"
    assert result["blockers"] == []


def test_preflight_requires_contextual_citation_audit(tmp_path):
    wd = tmp_path / "run"
    clear_required_artifacts(wd)
    (wd / "08-readiness/citation-support-audit.json").unlink()
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    assert result["status"] == "BLOCKED"
    assert any(x["area"] == "citation_support" and x["code"] == "ARTIFACT_MISSING" for x in result["blockers"])


def test_latex_build_requires_real_compile_and_official_template_provenance(tmp_path):
    wd = tmp_path / "run"
    clear_required_artifacts(wd)
    tex = wd / "05-template/build/main.tex"
    tex.parent.mkdir(parents=True, exist_ok=True)
    tex.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    codes = {x["code"] for x in result["blockers"]}
    assert "LATEX_NOT_COMPILED" in codes
    assert "OFFICIAL_TEMPLATE_PROVENANCE" in codes


def test_preflight_blocks_missing_artifacts(tmp_path):
    wd = tmp_path / "run"
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    assert result["status"] == "BLOCKED"
    assert any(x["code"] == "ARTIFACT_MISSING" for x in result["blockers"])
