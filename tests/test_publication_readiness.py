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
from readiness.reference_verifier import normalize_doi  # noqa: E402
from readiness.submission_preflight import run as preflight_run  # noqa: E402


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
