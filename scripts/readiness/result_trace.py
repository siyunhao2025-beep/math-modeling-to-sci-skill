#!/usr/bin/env python3
"""Audit manuscript-result declarations against recorded producing runs.

This is a deterministic contract check.  It does not execute analyses, infer
units, or decide whether a model or scientific claim is correct.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import load_json, save_json  # noqa: E402


SHA256_RE = re.compile(r"[a-f0-9]{64}$")
CLASSIFICATIONS = {"MATCH", "MISMATCH", "UNVERIFIABLE"}
LOCK_BASES = {"version_control_commit", "external_registration", "immutable_record"}
RUN_PURPOSES = {"SCIENTIFIC_EVIDENCE", "PIPELINE_SMOKE", "RESOURCE_CALIBRATION"}
CLAIM_ROLES = {"scientific_result", "pipeline_function", "resource_cost"}
ROLE_PURPOSES = {
    "scientific_result": {"SCIENTIFIC_EVIDENCE"},
    "pipeline_function": {"SCIENTIFIC_EVIDENCE", "PIPELINE_SMOKE"},
    "resource_cost": {"SCIENTIFIC_EVIDENCE", "RESOURCE_CALIBRATION"},
}
PREDICATES = {
    "<": lambda value, threshold: value < threshold,
    "<=": lambda value, threshold: value <= threshold,
    ">": lambda value, threshold: value > threshold,
    ">=": lambda value, threshold: value >= threshold,
    "==": lambda value, threshold: value == threshold,
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not _text(value):
        errors.append(f"{field} must be a timezone-aware ISO-8601 timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be a timezone-aware ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{field} must be timezone-aware")
        return None
    return parsed


def _lock_time(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return None
    if value.get("basis") not in LOCK_BASES:
        errors.append(f"{field}.basis must be one of {sorted(LOCK_BASES)}")
    if not _text(value.get("locator")):
        errors.append(f"{field}.locator must identify the immutable record")
    if not _sha256(value.get("sha256")):
        errors.append(f"{field}.sha256 must be a lowercase SHA-256")
    return _timestamp(value.get("recorded_at"), f"{field}.recorded_at", errors)


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


def _invalid_result(message: str) -> dict:
    return {
        "verdict": "BLOCKED",
        "counts": {"MATCH": 0, "MISMATCH": 0, "UNVERIFIABLE": 0},
        "errors": [message],
        "scope": "declared_manuscript_values_to_recorded_runs",
        "scientific_correctness_implied": False,
        "important_limit": (
            "This audit checks declared lock metadata, timing, roles, and trace logic; "
            "it does not retrieve an external lock record, rerun the analysis, or "
            "establish model validity or scientific correctness."
        ),
    }


def audit_ledger(payload: Any) -> dict:
    """Validate a frozen value inventory and its explicit run comparisons."""
    if not isinstance(payload, dict):
        return _invalid_result("ledger must be a JSON object")

    errors: list[str] = []
    counts = {"MATCH": 0, "MISMATCH": 0, "UNVERIFIABLE": 0}
    if payload.get("schema_version") != "1.1":
        errors.append("schema_version must be 1.1")

    inventory = payload.get("inventory")
    if not isinstance(inventory, dict):
        errors.append("inventory must be an object")
        inventory = {}
    if not _sha256(inventory.get("manuscript_sha256")):
        errors.append("inventory.manuscript_sha256 must be a lowercase SHA-256")
    scope = inventory.get("scope")
    if (not isinstance(scope, list) or not scope
            or any(not _text(item) for item in scope)
            or len(scope) != len(set(scope))):
        errors.append("inventory.scope must be a non-empty unique string array")
    if inventory.get("complete_for_scope") is not True:
        errors.append("inventory.complete_for_scope must be true")
    if inventory.get("frozen_before_execution") is not True:
        errors.append("inventory.frozen_before_execution must be true")
    inventory_lock_at = _lock_time(inventory.get("lock"), "inventory.lock", errors)

    runs = payload.get("runs")
    run_index: dict[str, dict] = {}
    run_times: dict[str, tuple[datetime | None, datetime | None]] = {}
    if not isinstance(runs, list) or not runs:
        errors.append("runs must be a non-empty array")
        runs = []
    for index, run in enumerate(runs):
        label = f"runs[{index}]"
        if not isinstance(run, dict):
            errors.append(f"{label} must be an object")
            continue
        run_id = run.get("run_id")
        if not _text(run_id):
            errors.append(f"{label}.run_id must be a non-empty string")
            continue
        if run_id in run_index:
            errors.append(f"duplicate run_id: {run_id}")
            continue
        run_index[run_id] = run
        if run.get("status") != "COMPLETED":
            errors.append(f"run {run_id} status must be COMPLETED")
        if run.get("purpose") not in RUN_PURPOSES:
            errors.append(f"run {run_id} purpose must be one of {sorted(RUN_PURPOSES)}")
        started_at = _timestamp(run.get("started_at"), f"run {run_id} started_at", errors)
        completed_at = _timestamp(run.get("completed_at"), f"run {run_id} completed_at", errors)
        run_times[run_id] = (started_at, completed_at)
        if started_at is not None and completed_at is not None and completed_at < started_at:
            errors.append(f"run {run_id} completed_at must not precede started_at")
        for field in ("command", "environment"):
            if not _text(run.get(field)):
                errors.append(f"run {run_id} needs a non-empty {field}")
        inputs = run.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"run {run_id} inputs must be a non-empty array")
        else:
            input_ids: set[str] = set()
            for input_index, item in enumerate(inputs):
                if not isinstance(item, dict) or not _text(item.get("id")):
                    errors.append(f"run {run_id} input {input_index} needs an id")
                    continue
                if item["id"] in input_ids:
                    errors.append(f"run {run_id} has duplicate input id: {item['id']}")
                input_ids.add(item["id"])
                if not _sha256(item.get("sha256")):
                    errors.append(f"run {run_id} input {item['id']} needs a lowercase SHA-256")
        if not isinstance(run.get("deterministic"), bool):
            errors.append(f"run {run_id} deterministic must be boolean")
        elif run["deterministic"] is False and run.get("seed") is None:
            errors.append(f"run {run_id} needs a recorded seed when deterministic is false")

    if inventory_lock_at is not None:
        for run_id, (started_at, _) in run_times.items():
            if started_at is not None and inventory_lock_at >= started_at:
                errors.append(f"inventory.lock.recorded_at must predate run {run_id} started_at")

    values = payload.get("values")
    if not isinstance(values, list) or not values:
        errors.append("values must be a non-empty array")
        values = []
    value_ids: set[str] = set()
    for index, value in enumerate(values):
        label = f"values[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{label} must be an object")
            continue
        value_id = value.get("value_id")
        if not _text(value_id):
            errors.append(f"{label}.value_id must be a non-empty string")
            value_id = label
        elif value_id in value_ids:
            errors.append(f"duplicate value_id: {value_id}")
        value_ids.add(value_id)
        for field in ("claim_id", "location", "reported_text", "reported_unit"):
            if not _text(value.get(field)):
                errors.append(f"value {value_id} needs a non-empty {field}")
        claim_role = value.get("claim_role")
        if claim_role not in CLAIM_ROLES:
            errors.append(f"value {value_id} claim_role must be one of {sorted(CLAIM_ROLES)}")

        classification = value.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append(f"value {value_id} has an invalid classification")
            continue
        counts[classification] += 1
        if classification == "UNVERIFIABLE":
            if not _text(value.get("reason")):
                errors.append(f"UNVERIFIABLE value {value_id} needs a reason")
            if "comparison" in value:
                errors.append(f"UNVERIFIABLE value {value_id} must not declare a comparison")
            continue

        run_id = value.get("run_id")
        if run_id not in run_index:
            errors.append(f"value {value_id} references an unknown run_id")
        elif claim_role in ROLE_PURPOSES:
            run_purpose = run_index[run_id].get("purpose")
            if run_purpose not in ROLE_PURPOSES[claim_role]:
                errors.append(
                    f"value {value_id} claim_role {claim_role} cannot be backed by "
                    f"run purpose {run_purpose}"
                )
        comparison = value.get("comparison")
        if not isinstance(comparison, dict):
            errors.append(f"value {value_id} needs a comparison object")
            continue
        if comparison.get("rule_frozen_before_execution") is not True:
            errors.append(f"value {value_id} comparison rule was not frozen before execution")
        rule_lock_at = _lock_time(
            comparison.get("rule_lock"),
            f"value {value_id} comparison.rule_lock",
            errors,
        )
        started_at = run_times.get(run_id, (None, None))[0]
        if rule_lock_at is not None and started_at is not None and rule_lock_at >= started_at:
            errors.append(
                f"value {value_id} comparison.rule_lock.recorded_at must predate "
                f"run {run_id} started_at"
            )
        computed = _decimal(
            comparison.get("computed_in_reported_unit"),
            f"value {value_id} comparison.computed_in_reported_unit",
            errors,
        )
        actual_match: bool | None = None
        boundary = False
        kind = comparison.get("kind")
        if kind == "interval":
            lower = _decimal(comparison.get("lower"), f"value {value_id} interval.lower", errors)
            upper = _decimal(comparison.get("upper"), f"value {value_id} interval.upper", errors)
            lower_inclusive = comparison.get("lower_inclusive")
            upper_inclusive = comparison.get("upper_inclusive")
            if not isinstance(lower_inclusive, bool) or not isinstance(upper_inclusive, bool):
                errors.append(f"value {value_id} interval inclusivity must be explicit booleans")
            elif lower is not None and upper is not None and computed is not None:
                if lower > upper:
                    errors.append(f"value {value_id} interval lower exceeds upper")
                else:
                    lower_ok = computed >= lower if lower_inclusive else computed > lower
                    upper_ok = computed <= upper if upper_inclusive else computed < upper
                    actual_match = lower_ok and upper_ok
                    boundary = computed == lower or computed == upper
        elif kind == "predicate":
            operator = comparison.get("operator")
            threshold = _decimal(
                comparison.get("threshold"), f"value {value_id} predicate.threshold", errors
            )
            if operator not in PREDICATES:
                errors.append(f"value {value_id} has an invalid predicate operator")
            elif threshold is not None and computed is not None:
                actual_match = PREDICATES[operator](computed, threshold)
                boundary = computed == threshold
        else:
            errors.append(f"value {value_id} comparison kind must be interval or predicate")

        if boundary and value.get("boundary_case_disclosed") is not True:
            errors.append(f"value {value_id} boundary case must be explicitly disclosed")
        if actual_match is not None:
            actual = "MATCH" if actual_match else "MISMATCH"
            if classification != actual:
                errors.append(
                    f"value {value_id} classification {classification} disagrees with frozen comparison ({actual})"
                )
        if classification == "MISMATCH" and not _text(value.get("author_action")):
            errors.append(f"MISMATCH value {value_id} needs an author_action")

    if errors or counts["UNVERIFIABLE"]:
        verdict = "BLOCKED"
    elif counts["MISMATCH"]:
        verdict = "AUTHOR_ACTION_REQUIRED"
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "counts": counts,
        "errors": errors,
        "scope": "declared_manuscript_values_to_recorded_runs",
        "scientific_correctness_implied": False,
        "important_limit": (
            "This audit checks declared lock metadata, timing, roles, and trace logic; "
            "it does not retrieve an external lock record, rerun the analysis, or "
            "establish model validity or scientific correctness."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a frozen manuscript-value inventory against recorded producing runs."
    )
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    output = Path(args.out)
    if output.exists():
        print("result trace: BLOCKED - output exists; use a new path", file=sys.stderr)
        return 2
    try:
        result = audit_ledger(load_json(args.ledger))
        save_json(output, result)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"result trace: BLOCKED - {exc}", file=sys.stderr)
        return 2
    print(f"result trace: {result['verdict']} -> {output}")
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
