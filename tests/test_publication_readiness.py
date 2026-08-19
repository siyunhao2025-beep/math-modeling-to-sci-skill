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


def test_preflight_can_reach_human_check_when_all_required_artifacts_clear(tmp_path):
    wd = tmp_path / "run"
    dump(wd / "06-validate/validation-final.json", {
        "summary": {"error_count": 0, "unresolved_error_ids": []},
        "checkers": [{"name": "latex_compile_check", "status": "pass", "findings": []}],
    })
    dump(wd / "08-readiness/reference-verification.json", {"blockers": []})
    dump(wd / "08-readiness/journal-fit.json", {"blockers": [], "baseline_fit_score_0_100": 90})
    dump(wd / "08-readiness/claim-evidence-audit.json", {"blockers": [], "claims": []})
    dump(wd / "08-readiness/figure-table-audit.json", {"blockers": [], "visual_scientific_review": "PASS"})
    dump(wd / "08-readiness/compliance-audit.json", {"blockers": [], "recommended_reporting_guidelines": []})
    dump(wd / "08-readiness/reviewer-simulation.json", {"comments": [
        {"id": "RS-1", "severity": "major", "status": "RESOLVED"},
        {"id": "RS-2", "severity": "major", "status": "RESOLVED"},
        {"id": "RS-3", "severity": "minor", "status": "RESOLVED"},
    ]})
    dump(wd / "08-readiness/citation-support-audit.json", {"citations": [], "blockers": []})
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    assert result["status"] == "READY_FOR_HUMAN_SUBMISSION_CHECK"
    assert result["blockers"] == []


def test_preflight_blocks_missing_artifacts(tmp_path):
    wd = tmp_path / "run"
    out = wd / "08-readiness/submission-preflight.json"
    result = preflight_run(str(wd), str(out))
    assert result["status"] == "BLOCKED"
    assert any(x["code"] == "ARTIFACT_MISSING" for x in result["blockers"])
