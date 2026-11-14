from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from readiness import result_trace  # noqa: E402


def _payload() -> dict:
    return {
        "schema_version": "1.1",
        "inventory": {
            "manuscript_sha256": "a" * 64,
            "scope": ["Abstract", "Results"],
            "complete_for_scope": True,
            "frozen_before_execution": True,
            "lock": {
                "basis": "version_control_commit",
                "locator": "git:fixture/result-trace@abc123",
                "sha256": "c" * 64,
                "recorded_at": "2026-10-09T08:00:00+08:00",
            },
        },
        "runs": [
            {
                "run_id": "run-1",
                "status": "COMPLETED",
                "purpose": "SCIENTIFIC_EVIDENCE",
                "started_at": "2026-10-09T09:00:00+08:00",
                "completed_at": "2026-10-09T09:10:00+08:00",
                "command": "python analysis/run.py --config locked.json",
                "environment": "Python 3.12; requirements.lock sha256:fixture",
                "inputs": [{"id": "dataset", "sha256": "b" * 64}],
                "deterministic": True,
                "seed": 7,
            }
        ],
        "values": [
            {
                "value_id": "v-mean",
                "claim_id": "C-1",
                "location": "Results, Table 2",
                "reported_text": "83.41%",
                "reported_unit": "percent",
                "claim_role": "scientific_result",
                "classification": "MATCH",
                "run_id": "run-1",
                "comparison": {
                    "kind": "interval",
                    "computed_in_reported_unit": "83.4125",
                    "lower": "83.405",
                    "upper": "83.415",
                    "lower_inclusive": True,
                    "upper_inclusive": False,
                    "rule_frozen_before_execution": True,
                    "rule_lock": {
                        "basis": "version_control_commit",
                        "locator": "git:fixture/comparison-rules@def456",
                        "sha256": "d" * 64,
                        "recorded_at": "2026-10-09T08:30:00+08:00",
                    },
                },
            }
        ],
    }


def test_matching_value_with_run_and_input_provenance_passes():
    result = result_trace.audit_ledger(_payload())
    assert result["verdict"] == "PASS"
    assert result["counts"] == {"MATCH": 1, "MISMATCH": 0, "UNVERIFIABLE": 0}
    assert result["errors"] == []


def test_declared_match_cannot_disagree_with_predeclared_interval():
    payload = _payload()
    payload["values"][0]["comparison"]["computed_in_reported_unit"] = "83.50"
    result = result_trace.audit_ledger(payload)
    assert result["verdict"] == "BLOCKED"
    assert any("classification" in item for item in result["errors"])


def test_mismatch_requires_author_action_and_keeps_the_adverse_result():
    payload = _payload()
    value = payload["values"][0]
    value["classification"] = "MISMATCH"
    value["comparison"]["computed_in_reported_unit"] = "82.90"
    value["author_action"] = "Reconcile the table, abstract, and discussion before release."
    result = result_trace.audit_ledger(payload)
    assert result["verdict"] == "AUTHOR_ACTION_REQUIRED"
    assert result["counts"]["MISMATCH"] == 1


def test_unverifiable_value_is_not_promoted_to_a_match():
    payload = _payload()
    value = payload["values"][0]
    value["classification"] = "UNVERIFIABLE"
    value.pop("run_id")
    value.pop("comparison")
    value["reason"] = "The manuscript does not identify a producing command."
    result = result_trace.audit_ledger(payload)
    assert result["verdict"] == "BLOCKED"
    assert result["counts"]["UNVERIFIABLE"] == 1


def test_interval_endpoint_requires_explicit_boundary_disclosure():
    payload = _payload()
    payload["values"][0]["comparison"]["computed_in_reported_unit"] = "83.405"
    result = result_trace.audit_ledger(payload)
    assert result["verdict"] == "BLOCKED"
    assert any("boundary" in item for item in result["errors"])

    payload["values"][0]["boundary_case_disclosed"] = True
    assert result_trace.audit_ledger(payload)["verdict"] == "PASS"


def test_predicate_comparison_is_checked_without_unit_guessing():
    payload = _payload()
    value = payload["values"][0]
    rule_lock = copy.deepcopy(value["comparison"]["rule_lock"])
    value["reported_text"] = "p < 0.001"
    value["reported_unit"] = "dimensionless"
    value["comparison"] = {
        "kind": "predicate",
        "operator": "<",
        "threshold": "0.001",
        "computed_in_reported_unit": "0.0004",
        "rule_frozen_before_execution": True,
        "rule_lock": rule_lock,
    }
    assert result_trace.audit_ledger(payload)["verdict"] == "PASS"


def test_self_attested_freeze_without_lock_evidence_is_blocked():
    payload = _payload()
    payload["inventory"].pop("lock")
    payload["values"][0]["comparison"].pop("rule_lock")

    result = result_trace.audit_ledger(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("inventory.lock" in item for item in result["errors"])
    assert any("comparison.rule_lock" in item for item in result["errors"])


def test_lock_recorded_after_run_start_cannot_count_as_predeclared():
    payload = _payload()
    payload["values"][0]["comparison"]["rule_lock"]["recorded_at"] = (
        "2026-10-09T09:00:01+08:00"
    )

    result = result_trace.audit_ledger(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("must predate" in item for item in result["errors"])


def test_pipeline_smoke_run_cannot_back_a_scientific_result():
    payload = _payload()
    payload["runs"][0]["purpose"] = "PIPELINE_SMOKE"

    result = result_trace.audit_ledger(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("scientific_result" in item for item in result["errors"])


def test_resource_calibration_can_only_back_resource_cost_claims():
    payload = _payload()
    payload["runs"][0]["purpose"] = "RESOURCE_CALIBRATION"
    payload["values"][0]["claim_role"] = "resource_cost"

    assert result_trace.audit_ledger(payload)["verdict"] == "PASS"


def test_run_timestamps_must_be_timezone_aware_and_ordered():
    payload = _payload()
    payload["runs"][0]["started_at"] = "2026-10-09T09:00:00"

    result = result_trace.audit_ledger(payload)

    assert result["verdict"] == "BLOCKED"
    assert any("timezone-aware" in item for item in result["errors"])

    payload["runs"][0]["started_at"] = "2026-10-09T09:00:00+08:00"
    payload["runs"][0]["completed_at"] = "2026-10-09T08:59:59+08:00"
    result = result_trace.audit_ledger(payload)

    assert any("completed_at" in item for item in result["errors"])


def test_cli_refuses_to_overwrite_a_previous_audit(tmp_path):
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "audit.json"
    ledger.write_text(json.dumps(_payload()), encoding="utf-8")

    assert result_trace.main(["--ledger", str(ledger), "--out", str(output)]) == 0
    first = output.read_bytes()
    assert result_trace.main(["--ledger", str(ledger), "--out", str(output)]) == 2
    assert output.read_bytes() == first


def test_duplicate_value_ids_are_rejected():
    payload = _payload()
    payload["values"].append(copy.deepcopy(payload["values"][0]))
    result = result_trace.audit_ledger(payload)
    assert result["verdict"] == "BLOCKED"
    assert any("duplicate value_id" in item for item in result["errors"])
