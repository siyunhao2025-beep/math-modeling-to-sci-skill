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
        "schema_version": "1.0",
        "inventory": {
            "manuscript_sha256": "a" * 64,
            "scope": ["Abstract", "Results"],
            "complete_for_scope": True,
            "frozen_before_execution": True,
        },
        "runs": [
            {
                "run_id": "run-1",
                "status": "COMPLETED",
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
    value["reported_text"] = "p < 0.001"
    value["reported_unit"] = "dimensionless"
    value["comparison"] = {
        "kind": "predicate",
        "operator": "<",
        "threshold": "0.001",
        "computed_in_reported_unit": "0.0004",
        "rule_frozen_before_execution": True,
    }
    assert result_trace.audit_ledger(payload)["verdict"] == "PASS"


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
