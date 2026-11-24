#!/usr/bin/env python3
"""Validate a claim-impact decision before commissioning another model run.

This is a deterministic contract check. It does not choose scientific
thresholds, execute a model, or decide whether a claim is true.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import load_json, save_json  # noqa: E402


CLAIM_LEVELS = {
    "QUALITATIVE",
    "COMPARATIVE",
    "QUANTITATIVE",
    "INFERENTIAL",
    "MECHANISTIC",
}
UNCERTAINTY_CLASSES = {
    "IMPLEMENTATION_CORRECTNESS",
    "STOCHASTIC_VARIATION",
    "NUMERICAL_ADEQUACY",
    "MODEL_FORM",
    "EXTERNAL_DISCREPANCY",
}
MINIMUM_STATUSES = {"COMPLETE", "INCOMPLETE"}
CORRECTNESS_STATUSES = {"PASS", "FAIL", "UNRESOLVED"}
SCALE_STATUSES = {"QUANTIFIED", "NOT_COMPARABLE"}
CLAIM_IMPACTS = {"NONE", "NARROW", "WITHDRAW", "ESCALATE"}
OUTCOME_DIRECTIONS = {"SUPPORTIVE", "ADVERSE", "INCONCLUSIVE"}
ACTIONS = {
    "STOP_AND_REPORT",
    "BOUNDED_VALIDATION",
    "CLAIM_NOT_SUPPORTED",
    "HUMAN_ADJUDICATION",
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_text(item) for item in value)


def _decimal(value: Any, field: str, errors: list[str]) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        errors.append(f"{field} must be an explicit finite decimal")
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"{field} must be an explicit finite decimal")
        return None
    if not parsed.is_finite():
        errors.append(f"{field} must be finite")
        return None
    return parsed


def _audit_scale_comparison(value: Any, errors: list[str], warnings: list[str]) -> None:
    field = "scale_comparison"
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    status = value.get("status")
    if status not in SCALE_STATUSES:
        errors.append(f"{field}.status must be one of {sorted(SCALE_STATUSES)}")
        return
    if status == "NOT_COMPARABLE":
        if not _text(value.get("reason")):
            errors.append(f"{field}.reason is required when scales are not comparable")
        warnings.append(
            "The effect/decision boundary and uncertainty were declared not comparable; "
            "the scientific interpretation remains a manual judgment."
        )
        return

    effect = value.get("effect_or_boundary")
    uncertainty = value.get("uncertainty")
    if not isinstance(effect, dict):
        errors.append(f"{field}.effect_or_boundary must be an object")
        effect = {}
    if not isinstance(uncertainty, dict):
        errors.append(f"{field}.uncertainty must be an object")
        uncertainty = {}
    _decimal(effect.get("value"), f"{field}.effect_or_boundary.value", errors)
    uncertainty_value = _decimal(
        uncertainty.get("value"), f"{field}.uncertainty.value", errors
    )
    if uncertainty_value is not None and uncertainty_value < 0:
        errors.append(f"{field}.uncertainty.value must be non-negative")
    effect_unit = effect.get("unit")
    uncertainty_unit = uncertainty.get("unit")
    if not _text(effect_unit):
        errors.append(f"{field}.effect_or_boundary.unit must be a non-empty string")
    if not _text(uncertainty_unit):
        errors.append(f"{field}.uncertainty.unit must be a non-empty string")
    if _text(effect_unit) and _text(uncertainty_unit) and effect_unit != uncertainty_unit:
        errors.append(f"{field} quantities must use the same reported unit")
    if not _text(value.get("interpretation")):
        errors.append(f"{field}.interpretation must state why the comparison matters")


def audit_triage(payload: Any) -> dict:
    """Return a machine-readable contract verdict for one proposed validation decision."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return _result("BLOCKED", None, ["triage input must be a JSON object"], warnings)
    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    claim = payload.get("claim")
    if not isinstance(claim, dict):
        errors.append("claim must be an object")
        claim = {}
    for field in ("claim_id", "text", "evidence_ceiling"):
        if not _text(claim.get(field)):
            errors.append(f"claim.{field} must be a non-empty string")
    if claim.get("level") not in CLAIM_LEVELS:
        errors.append(f"claim.level must be one of {sorted(CLAIM_LEVELS)}")

    minimum = payload.get("minimum_obligations")
    if not isinstance(minimum, dict):
        errors.append("minimum_obligations must be an object")
        minimum = {}
    minimum_status = minimum.get("status")
    if minimum_status not in MINIMUM_STATUSES:
        errors.append(
            f"minimum_obligations.status must be one of {sorted(MINIMUM_STATUSES)}"
        )
    elif minimum_status == "COMPLETE" and not _text_list(minimum.get("evidence")):
        errors.append("complete minimum_obligations need a non-empty evidence list")
    elif minimum_status == "INCOMPLETE" and not _text_list(minimum.get("missing")):
        errors.append("incomplete minimum_obligations need a non-empty missing list")

    correctness = payload.get("implementation_correctness")
    if not isinstance(correctness, dict):
        errors.append("implementation_correctness must be an object")
        correctness = {}
    correctness_status = correctness.get("status")
    if correctness_status not in CORRECTNESS_STATUSES:
        errors.append(
            "implementation_correctness.status must be one of "
            f"{sorted(CORRECTNESS_STATUSES)}"
        )
    if not _text_list(correctness.get("evidence")):
        errors.append("implementation_correctness.evidence must be a non-empty list")

    uncertainty = payload.get("uncertainty_classes")
    declared_classes: set[str] = set()
    if not isinstance(uncertainty, list) or not uncertainty:
        errors.append("uncertainty_classes must be a non-empty array")
        uncertainty = []
    for index, entry in enumerate(uncertainty):
        label = f"uncertainty_classes[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        name = entry.get("class")
        if name not in UNCERTAINTY_CLASSES:
            errors.append(f"{label}.class must be one of {sorted(UNCERTAINTY_CLASSES)}")
        elif name in declared_classes:
            errors.append(f"duplicate uncertainty class: {name}")
        else:
            declared_classes.add(name)
        for field in ("evidence", "decision_relevance"):
            if not _text(entry.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")

    if not _text(payload.get("decision_boundary")):
        errors.append("decision_boundary must be a non-empty string")
    _audit_scale_comparison(payload.get("scale_comparison"), errors, warnings)

    proposed = payload.get("proposed_test")
    if not isinstance(proposed, dict):
        errors.append("proposed_test must be an object")
        proposed = {}
    for field in ("test_id", "description"):
        if not _text(proposed.get(field)):
            errors.append(f"proposed_test.{field} must be a non-empty string")
    targets = proposed.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("proposed_test.targets must be a non-empty array")
        targets = []
    elif any(item not in declared_classes for item in targets):
        errors.append("proposed_test.targets must reference declared uncertainty classes")
    elif len(set(targets)) != len(targets):
        errors.append("proposed_test.targets must not contain duplicates")

    outcomes = proposed.get("outcomes")
    impacts: list[str] = []
    directions: list[str] = []
    outcome_ids: set[str] = set()
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        errors.append("proposed_test.outcomes must contain at least two plausible outcomes")
        outcomes = []
    for index, outcome in enumerate(outcomes):
        label = f"proposed_test.outcomes[{index}]"
        if not isinstance(outcome, dict):
            errors.append(f"{label} must be an object")
            continue
        outcome_id = outcome.get("outcome_id")
        if not _text(outcome_id):
            errors.append(f"{label}.outcome_id must be a non-empty string")
        elif outcome_id in outcome_ids:
            errors.append(f"duplicate outcome_id: {outcome_id}")
        else:
            outcome_ids.add(outcome_id)
        for field in ("condition", "wording_action"):
            if not _text(outcome.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        impact = outcome.get("claim_impact")
        if impact not in CLAIM_IMPACTS:
            errors.append(f"{label}.claim_impact must be one of {sorted(CLAIM_IMPACTS)}")
        else:
            impacts.append(impact)
        direction = outcome.get("direction")
        if direction not in OUTCOME_DIRECTIONS:
            errors.append(
                f"{label}.direction must be one of {sorted(OUTCOME_DIRECTIONS)}"
            )
        else:
            directions.append(direction)
    if outcomes and "ADVERSE" not in directions:
        errors.append("proposed_test.outcomes must include an ADVERSE branch")
    if outcomes and not any(item in {"SUPPORTIVE", "INCONCLUSIVE"} for item in directions):
        errors.append("proposed_test.outcomes must include a SUPPORTIVE or INCONCLUSIVE branch")

    decision = payload.get("decision")
    if not isinstance(decision, dict):
        errors.append("decision must be an object")
        decision = {}
    action = decision.get("action")
    if action not in ACTIONS:
        errors.append(f"decision.action must be one of {sorted(ACTIONS)}")
        action = None
    if not _text(decision.get("rationale")):
        errors.append("decision.rationale must be a non-empty string")

    if action == "STOP_AND_REPORT":
        if minimum_status != "COMPLETE":
            errors.append("STOP_AND_REPORT requires complete minimum obligations")
        if correctness_status != "PASS":
            errors.append("STOP_AND_REPORT requires implementation correctness PASS")
        if any(impact != "NONE" for impact in impacts):
            errors.append("STOP_AND_REPORT requires every plausible outcome to leave the claim unchanged")
        if decision.get("author_confirmation") is not True:
            errors.append("STOP_AND_REPORT requires author_confirmation=true")
    elif action == "BOUNDED_VALIDATION":
        if not _text(proposed.get("bounded_budget")):
            errors.append("BOUNDED_VALIDATION requires proposed_test.bounded_budget")
        if not _text(proposed.get("stop_rule")):
            errors.append("BOUNDED_VALIDATION requires proposed_test.stop_rule")
        if impacts and all(impact == "NONE" for impact in impacts):
            errors.append("BOUNDED_VALIDATION needs at least one outcome that changes the claim")
        if correctness_status == "FAIL" and "IMPLEMENTATION_CORRECTNESS" not in targets:
            errors.append(
                "failed implementation correctness can only be tested by targeting "
                "IMPLEMENTATION_CORRECTNESS"
            )
    elif action == "CLAIM_NOT_SUPPORTED":
        if decision.get("claim_disposition") not in {"NARROW", "WITHDRAW"}:
            errors.append("CLAIM_NOT_SUPPORTED requires claim_disposition NARROW or WITHDRAW")
        if not _text(decision.get("replacement_wording")):
            errors.append("CLAIM_NOT_SUPPORTED requires replacement_wording")
        if decision.get("author_confirmation") is not True:
            errors.append("CLAIM_NOT_SUPPORTED requires author_confirmation=true")
    elif action == "HUMAN_ADJUDICATION":
        if not _text(decision.get("human_owner")):
            errors.append("HUMAN_ADJUDICATION requires human_owner")
        if not _text(decision.get("question")):
            errors.append("HUMAN_ADJUDICATION requires question")

    verdict = "BLOCKED" if errors else "CONTRACT_VALID"
    return _result(verdict, action, errors, warnings)


def _result(
    verdict: str,
    action: str | None,
    errors: list[str],
    warnings: list[str],
) -> dict:
    return {
        "verdict": verdict,
        "action": action,
        "run_additional_validation": action == "BOUNDED_VALIDATION" and not errors,
        "errors": errors,
        "warnings": warnings,
        "scope": "claim_impact_validation_triage",
        "scientific_correctness_implied": False,
        "release_readiness_implied": False,
        "important_limit": (
            "This audit checks the declared triage contract. It does not establish that the "
            "outcome set is exhaustive, execute a model, verify evidence, choose scientific "
            "thresholds, or establish that a claim is true."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a claim-impact decision before another model-validation run."
    )
    parser.add_argument("--triage", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    output = Path(args.out)
    if output.exists():
        print("validation triage: BLOCKED - output exists; use a new path", file=sys.stderr)
        return 2
    try:
        result = audit_triage(load_json(args.triage))
        save_json(output, result)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"validation triage: BLOCKED - {exc}", file=sys.stderr)
        return 2
    print(f"validation triage: {result['verdict']} -> {output}")
    return 0 if result["verdict"] == "CONTRACT_VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
