from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from readiness import validation_triage  # noqa: E402


def _payload() -> dict:
    return {
        "schema_version": "1.0",
        "claim": {
            "claim_id": "C-robustness",
            "text": "The reported ranking is stable to the registered weight perturbations.",
            "level": "COMPARATIVE",
            "evidence_ceiling": "Registered perturbations and the observed data only.",
        },
        "minimum_obligations": {
            "status": "COMPLETE",
            "evidence": ["validation-matrix.json#ranking-stability"],
        },
        "implementation_correctness": {
            "status": "PASS",
            "evidence": ["tests/test_ranking.py::test_reference_case"],
        },
        "uncertainty_classes": [
            {
                "class": "NUMERICAL_ADEQUACY",
                "evidence": "The smallest observed rank margin is 0.08 score units.",
                "decision_relevance": "A larger numerical error could reverse the headline order.",
            }
        ],
        "decision_boundary": "A rank reversal changes the comparative claim.",
        "scale_comparison": {
            "status": "QUANTIFIED",
            "effect_or_boundary": {"value": "0.08", "unit": "score"},
            "uncertainty": {"value": "0.002", "unit": "score"},
            "interpretation": "The declared numerical uncertainty is below the smallest rank margin.",
        },
        "proposed_test": {
            "test_id": "V-next-grid",
            "description": "Repeat the registered perturbation matrix at a finer solver tolerance.",
            "targets": ["NUMERICAL_ADEQUACY"],
            "outcomes": [
                {
                    "outcome_id": "stable",
                    "condition": "No registered comparison changes order.",
                    "direction": "SUPPORTIVE",
                    "claim_impact": "NONE",
                    "wording_action": "Keep the bounded stability statement.",
                },
                {
                    "outcome_id": "bounded-drift",
                    "condition": "Scores move, but no registered comparison changes order.",
                    "direction": "ADVERSE",
                    "claim_impact": "NONE",
                    "wording_action": "Report the observed drift without changing the bounded claim.",
                },
            ],
        },
        "decision": {
            "action": "STOP_AND_REPORT",
            "rationale": "The candidate run cannot change the registered claim under either declared outcome.",
            "author_confirmation": True,
        },
    }


def test_complete_claim_impact_triage_can_stop_without_claiming_scientific_truth():
    result = validation_triage.audit_triage(_payload())

    assert result["verdict"] == "CONTRACT_VALID"
    assert result["action"] == "STOP_AND_REPORT"
    assert result["run_additional_validation"] is False
    assert result["scientific_correctness_implied"] is False
    assert result["release_readiness_implied"] is False


def test_stop_and_report_requires_minimum_validation_to_be_complete():
    payload = _payload()
    payload["minimum_obligations"] = {
        "status": "INCOMPLETE",
        "missing": ["external holdout"],
    }

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("complete minimum" in item for item in result["errors"])


def test_stop_and_report_requires_implementation_correctness_pass():
    payload = _payload()
    payload["implementation_correctness"]["status"] = "UNRESOLVED"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("correctness PASS" in item for item in result["errors"])


def test_stop_and_report_is_blocked_when_an_outcome_changes_the_claim():
    payload = _payload()
    payload["proposed_test"]["outcomes"][1]["claim_impact"] = "NARROW"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("leave the claim unchanged" in item for item in result["errors"])


def test_outcome_set_must_include_an_explicit_adverse_branch():
    payload = _payload()
    payload["proposed_test"]["outcomes"][1]["direction"] = "INCONCLUSIVE"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("ADVERSE branch" in item for item in result["errors"])


def test_stopping_requires_explicit_author_confirmation():
    payload = _payload()
    payload["decision"].pop("author_confirmation")

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("author_confirmation" in item for item in result["errors"])


def test_bounded_validation_needs_budget_stop_rule_and_claim_relevant_outcome():
    payload = _payload()
    payload["decision"] = {
        "action": "BOUNDED_VALIDATION",
        "rationale": "A rank reversal would narrow the comparative claim.",
    }
    payload["proposed_test"]["bounded_budget"] = "One tolerance level and three registered seeds."
    payload["proposed_test"]["stop_rule"] = "Stop after the registered matrix is complete."
    payload["proposed_test"]["outcomes"][1]["condition"] = (
        "At least one registered comparison changes order."
    )
    payload["proposed_test"]["outcomes"][1]["claim_impact"] = "NARROW"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "CONTRACT_VALID"
    assert result["run_additional_validation"] is True


def test_bounded_validation_does_not_allow_an_all_no_change_test():
    payload = _payload()
    payload["decision"] = {
        "action": "BOUNDED_VALIDATION",
        "rationale": "Run one more grid without a declared claim-changing branch.",
    }
    payload["proposed_test"]["bounded_budget"] = "One tolerance level."
    payload["proposed_test"]["stop_rule"] = "Stop after one run."

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("changes the claim" in item for item in result["errors"])


def test_failed_implementation_must_be_targeted_before_more_validation():
    payload = _payload()
    payload["decision"] = {
        "action": "BOUNDED_VALIDATION",
        "rationale": "Resolve an implementation discrepancy before scientific comparison.",
    }
    payload["implementation_correctness"]["status"] = "FAIL"
    payload["proposed_test"]["bounded_budget"] = "One reference-case repair run."
    payload["proposed_test"]["stop_rule"] = "Stop after the locked reference case."
    payload["proposed_test"]["outcomes"][1]["condition"] = (
        "The reference case still fails after the bounded repair."
    )
    payload["proposed_test"]["outcomes"][1]["claim_impact"] = "WITHDRAW"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("IMPLEMENTATION_CORRECTNESS" in item for item in result["errors"])


def test_quantified_scale_comparison_preserves_reported_units():
    payload = _payload()
    payload["scale_comparison"]["uncertainty"]["unit"] = "percent"

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("same reported unit" in item for item in result["errors"])


def test_not_comparable_scales_require_reason_and_remain_manual():
    payload = _payload()
    payload["scale_comparison"] = {
        "status": "NOT_COMPARABLE",
        "reason": "The external discrepancy is categorical rather than numeric.",
    }

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "CONTRACT_VALID"
    assert any("manual judgment" in item for item in result["warnings"])


def test_unsupported_claim_can_exit_only_with_explicit_disposition_and_wording():
    payload = _payload()
    payload["decision"] = {
        "action": "CLAIM_NOT_SUPPORTED",
        "rationale": "The current evidence does not support the comparative statement.",
        "claim_disposition": "WITHDRAW",
        "replacement_wording": "Report the two observed scores without a stability claim.",
        "author_confirmation": True,
    }

    assert validation_triage.audit_triage(payload)["verdict"] == "CONTRACT_VALID"

    payload["decision"].pop("replacement_wording")
    result = validation_triage.audit_triage(payload)
    assert result["verdict"] == "BLOCKED"
    assert any("replacement_wording" in item for item in result["errors"])


def test_human_adjudication_requires_named_owner_and_question():
    payload = _payload()
    payload["decision"] = {
        "action": "HUMAN_ADJUDICATION",
        "rationale": "The decision boundary is a domain judgment.",
    }

    result = validation_triage.audit_triage(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("human_owner" in item for item in result["errors"])
    assert any("question" in item for item in result["errors"])


def test_cli_writes_contract_report_and_refuses_overwrite(tmp_path):
    source = tmp_path / "triage.json"
    output = tmp_path / "audit.json"
    source.write_text(json.dumps(_payload()), encoding="utf-8")

    assert validation_triage.main(["--triage", str(source), "--out", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["verdict"] == "CONTRACT_VALID"
    assert validation_triage.main(["--triage", str(source), "--out", str(output)]) == 2
