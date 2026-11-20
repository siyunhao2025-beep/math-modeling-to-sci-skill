#!/usr/bin/env python3
"""Deterministic FORGE workspace scaffolding and contract checks.

This utility verifies files, hashes, required fields and declared dependency
propagation. It never claims that scientific reasoning, citation support or
journal fit is semantically correct merely because a contract passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlparse


PHASES = ("F", "O", "R", "G", "E")
PHASE_NAMES = {
    "F": "Fidelity",
    "O": "Opportunity",
    "R": "Revalidation",
    "G": "Grounding",
    "E": "Editorial",
}
PREFIX_PHASE = {
    "00-source": "F",
    "01-forensics": "F",
    "02-opportunity": "O",
    "03-revalidation": "R",
    "04-manuscript": "G",
    "05-editorial": "E",
}
ARCHETYPES = {
    "optimization",
    "evaluation",
    "prediction",
    "classification-cv",
    "mechanism",
    "signal",
    "spatial-graph",
    "simulation",
}
DISPOSITIONS = {"retain", "adapt", "supplement", "drop", "pending"}
MANUSCRIPT_NAMES = ("manuscript.md", "manuscript.tex", "manuscript.docx")
READY = "READY_FOR_HUMAN_SUBMISSION_CHECK"
ACCESS_RANK = {"metadata_only": 0, "abstract_only": 1, "full_text": 2, "project_result": 3}
MIN_ACCESS = {"background": 0, "method": 1, "quantitative": 2, "causal": 2, "mechanistic": 2}
FINAL_SIZE_TOLERANCE_MM = 0.1
SEMANTIC_FIGURE_TYPES = {"roadmap", "schematic"}
EDITABLE_FIGURE_FORMATS = {"svg", "drawio", "pptx"}
SEMANTIC_OBJECT_KINDS = {"node", "group", "label", "connector"}
CONTENT_DISPOSITIONS = {"retained", "merged", "omitted"}
VERIFICATION_DEPTHS = ("text_bound", "source_bound", "execution_bound", "render_bound")
VERIFICATION_RANK = {name: rank for rank, name in enumerate(VERIFICATION_DEPTHS)}
MIN_GATE_G_VERIFICATION = "source_bound"
INTEGRITY_STATUSES = {
    "NO_SIGNAL_FOUND", "RETRACTED", "WITHDRAWN", "REMOVED",
    "EXPRESSION_OF_CONCERN", "CORRECTED", "NOT_CHECKED",
}
FATAL_INTEGRITY_STATUSES = {
    "RETRACTED", "WITHDRAWN", "REMOVED", "EXPRESSION_OF_CONCERN",
}
CORRECTION_EFFECTS = {
    "NOT_APPLICABLE", "UNAFFECTED", "AFFECTS_CITED_CONTENT", "UNKNOWN",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_sha256(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and value == value.lower()
            and all(char in "0123456789abcdef" for char in value))


def is_positive_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)) and value > 0)


def is_timezone_aware_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def check_publication_integrity(cite: dict, citation_id: object, errors: list[str]) -> None:
    status = cite.get("integrity_status")
    effect = cite.get("correction_effect")
    if status not in INTEGRITY_STATUSES:
        errors.append(f"citation {citation_id!r} has invalid integrity_status {status!r}")
        return
    if effect not in CORRECTION_EFFECTS:
        errors.append(f"citation {citation_id!r} has invalid correction_effect {effect!r}")

    if status == "NOT_CHECKED":
        errors.append(f"citation {citation_id!r} integrity_status NOT_CHECKED requires author action")
        return

    if not is_https_url(cite.get("integrity_source_url")):
        errors.append(f"citation {citation_id!r} needs an HTTPS integrity_source_url")
    if not is_timezone_aware_timestamp(cite.get("integrity_checked_at")):
        errors.append(
            f"citation {citation_id!r} integrity_checked_at must be a timezone-aware ISO-8601 timestamp"
        )

    if status in FATAL_INTEGRITY_STATUSES:
        errors.append(f"citation {citation_id!r} has blocking integrity_status {status}")
        return

    if status == "CORRECTED":
        if effect == "AFFECTS_CITED_CONTENT":
            errors.append(
                f"citation {citation_id!r} correction_effect AFFECTS_CITED_CONTENT blocks support"
            )
        elif effect == "UNKNOWN":
            errors.append(f"citation {citation_id!r} correction_effect UNKNOWN requires author action")
        elif effect == "UNAFFECTED":
            if not is_https_url(cite.get("correction_locator")):
                errors.append(
                    f"citation {citation_id!r} needs an HTTPS correction_locator for CORRECTED"
                )
        else:
            errors.append(
                f"citation {citation_id!r} CORRECTED requires correction_effect "
                "UNAFFECTED, AFFECTS_CITED_CONTENT or UNKNOWN"
            )
    elif effect != "NOT_APPLICABLE":
        errors.append(
            f"citation {citation_id!r} may use correction_effect {effect!r} only with CORRECTED"
        )


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def check_editable_artifact(
        root: Path, fig: dict, errors: list[str], warnings: list[str]) -> None:
    """Validate an optional semantic editing contract for roadmap/schematic figures."""
    figure_id = fig.get("figure_id")
    figure_type = fig.get("figure_type")
    if figure_type is None:
        return
    if figure_type not in {"data", *SEMANTIC_FIGURE_TYPES}:
        errors.append(f"figure {figure_id!r} has invalid figure_type {figure_type!r}")
        return
    if figure_type not in SEMANTIC_FIGURE_TYPES:
        return

    artifact = fig.get("editable_artifact")
    if artifact is None:
        warnings.append(
            f"figure {figure_id!r} is a {figure_type} without editable_artifact; "
            "local object-level revision cannot be checked"
        )
        return
    if not isinstance(artifact, dict):
        errors.append(f"figure {figure_id!r} editable_artifact must be an object")
        return

    source = artifact.get("source")
    fmt = artifact.get("format")
    if fmt not in EDITABLE_FIGURE_FORMATS:
        errors.append(
            f"figure {figure_id!r} editable_artifact.format must be one of "
            f"{sorted(EDITABLE_FIGURE_FORMATS)}"
        )
    if not isinstance(source, str) or not source.strip():
        errors.append(f"figure {figure_id!r} editable_artifact.source is required")
    else:
        source_path = root / source
        if not inside(root, source_path) or not source_path.is_file():
            errors.append(f"figure {figure_id!r} editable source missing or unsafe: {source}")
        elif fmt in EDITABLE_FIGURE_FORMATS and source_path.suffix.lower() != f".{fmt}":
            errors.append(
                f"figure {figure_id!r} editable source suffix does not match format {fmt!r}"
            )

    objects = artifact.get("objects")
    if not isinstance(objects, list) or not objects:
        errors.append(f"figure {figure_id!r} editable_artifact.objects must be a non-empty list")
        return
    object_ids: list[str] = []
    for obj in objects:
        if not isinstance(obj, dict):
            errors.append(f"figure {figure_id!r} has a non-object semantic object entry")
            continue
        object_id = obj.get("object_id")
        kind = obj.get("kind")
        if not isinstance(object_id, str) or not object_id.strip():
            errors.append(f"figure {figure_id!r} has a semantic object without object_id")
            continue
        object_ids.append(object_id)
        if kind not in SEMANTIC_OBJECT_KINDS:
            errors.append(
                f"figure {figure_id!r} object {object_id!r} has invalid kind {kind!r}"
            )
    duplicates = sorted({item for item in object_ids if object_ids.count(item) > 1})
    if duplicates:
        errors.append(
            f"figure {figure_id!r} has duplicate semantic object IDs: {', '.join(duplicates)}"
        )
    known_ids = set(object_ids)
    for obj in objects:
        if not isinstance(obj, dict) or obj.get("kind") != "connector":
            continue
        object_id = obj.get("object_id")
        for endpoint in ("source_id", "target_id"):
            target = obj.get(endpoint)
            if target not in known_ids:
                errors.append(
                    f"figure {figure_id!r} connector {object_id!r} has unknown "
                    f"{endpoint} {target!r}"
                )

    ledger = artifact.get("content_ledger")
    if ledger is None:
        warnings.append(
            f"figure {figure_id!r} editable_artifact lacks content_ledger; "
            "diagram simplification cannot be checked for silent object loss"
        )
        return
    if not isinstance(ledger, dict):
        errors.append(f"figure {figure_id!r} content_ledger must be an object")
        return

    source_ids = ledger.get("source_object_ids")
    entries = ledger.get("entries")
    if (not isinstance(source_ids, list) or not source_ids
            or any(not isinstance(item, str) or not item.strip() for item in source_ids)):
        errors.append(
            f"figure {figure_id!r} content_ledger.source_object_ids must be a non-empty "
            "list of strings"
        )
        return
    duplicate_sources = sorted({item for item in source_ids if source_ids.count(item) > 1})
    if duplicate_sources:
        errors.append(
            f"figure {figure_id!r} content_ledger has duplicate source object IDs: "
            f"{', '.join(duplicate_sources)}"
        )
    if not isinstance(entries, list):
        errors.append(f"figure {figure_id!r} content_ledger.entries must be a list")
        return

    accounted: list[str] = []
    source_set = set(source_ids)
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"figure {figure_id!r} has a non-object content disposition")
            continue
        source_id = entry.get("source_id")
        action = entry.get("action")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"figure {figure_id!r} content disposition lacks source_id")
            continue
        accounted.append(source_id)
        if source_id not in source_set:
            errors.append(
                f"figure {figure_id!r} content disposition references unknown source_id "
                f"{source_id!r}"
            )
        if action not in CONTENT_DISPOSITIONS:
            errors.append(
                f"figure {figure_id!r} source object {source_id!r} has invalid action "
                f"{action!r}"
            )
            continue
        if action in {"retained", "merged"}:
            target_id = entry.get("target_id")
            if target_id not in known_ids:
                errors.append(
                    f"figure {figure_id!r} source object {source_id!r} has unknown "
                    f"target_id {target_id!r}"
                )
            if action == "merged" and not str(entry.get("reason") or "").strip():
                errors.append(
                    f"figure {figure_id!r} merged source object {source_id!r} needs a reason"
                )
        else:
            if not str(entry.get("reason") or "").strip():
                errors.append(
                    f"figure {figure_id!r} omitted source object {source_id!r} needs a reason"
                )
            evidence_bearing = entry.get("evidence_bearing")
            if not isinstance(evidence_bearing, bool):
                errors.append(
                    f"figure {figure_id!r} omitted source object {source_id!r} must declare "
                    "boolean evidence_bearing"
                )
            elif evidence_bearing and entry.get("author_approved") is not True:
                errors.append(
                    f"figure {figure_id!r} evidence-bearing omission {source_id!r} needs "
                    "author_approved=true"
                )

    duplicate_entries = sorted({item for item in accounted if accounted.count(item) > 1})
    if duplicate_entries:
        errors.append(
            f"figure {figure_id!r} content_ledger has duplicate dispositions for: "
            f"{', '.join(duplicate_entries)}"
        )
    missing = sorted(source_set - set(accounted))
    if missing:
        errors.append(
            f"figure {figure_id!r} content_ledger leaves source objects unaccounted: "
            f"{', '.join(missing)}"
        )


def log_event(root: Path, event: str, **fields: object) -> None:
    payload = {"at": now(), "event": event, **fields}
    path = root / "audit" / "events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def template_payloads() -> dict[str, object]:
    return {
        "01-forensics/asset-inventory.json": {
            "schema_version": "2.0", "complete": False, "assets": [],
            "note": "Inventory every section, equation, figure, table, citation, key number and conclusion."
        },
        "01-forensics/disposition-ledger.json": {
            "schema_version": "2.0", "complete": False, "entries": [],
            "allowed_actions": sorted(DISPOSITIONS)
        },
        "01-forensics/symbol-map.json": {"schema_version": "2.0", "symbols": []},
        "01-forensics/gaps.json": {"schema_version": "2.0", "gaps": []},
        "02-opportunity/research-positioning.json": {
            "schema_version": "2.0", "complete": False,
            "problem": "", "gap": "", "approach": "", "evidence": "",
            "contribution": "", "boundary": "", "conversion_status": "pending"
        },
        "02-opportunity/model-profile.json": {
            "schema_version": "2.0", "complete": False, "primary_archetype": "",
            "secondary_archetypes": [], "assumptions": [], "risks": []
        },
        "03-revalidation/validation-plan.json": {
            "schema_version": "2.0", "complete": False, "claims": []
        },
        "03-revalidation/run-log.json": {"schema_version": "2.0", "runs": []},
        "03-revalidation/validation-results.json": {
            "schema_version": "2.0", "complete": False, "baseline_status": "pending",
            "baseline_reason": "", "runs": [], "unresolved_blockers": []
        },
        "04-manuscript/claim-map.json": {
            "schema_version": "2.0", "complete": False, "claims": []
        },
        "04-manuscript/figure-manifest.json": {
            "schema_version": "2.0", "complete": False, "figures": [], "waiver_reason": ""
        },
        "04-manuscript/citation-audit.json": {
            "schema_version": "2.0", "complete": False, "citations": [], "blockers": []
        },
        "05-editorial/journal-evidence.json": {
            "schema_version": "2.0", "complete": False, "selected_journal": "", "candidates": []
        },
        "05-editorial/reviewer-panel.json": {
            "schema_version": "2.0", "complete": False, "reviewers": [], "verdict": "INCOMPLETE"
        },
        "05-editorial/submission-preflight.json": {
            "schema_version": "2.0", "complete": False, "status": "BLOCKED", "blockers": []
        },
    }


def command_init(args: argparse.Namespace) -> int:
    root = Path(args.workspace).expanduser().resolve()
    source = Path(args.input).expanduser().resolve()
    if not source.is_file():
        print(f"ERROR input file not found: {source}", file=sys.stderr)
        return 2
    root.mkdir(parents=True, exist_ok=True)
    for rel in ("00-source/snapshot", "01-forensics", "02-opportunity", "03-revalidation",
                "04-manuscript", "05-editorial", "audit"):
        (root / rel).mkdir(parents=True, exist_ok=True)

    digest = sha256(source)
    target = root / "00-source" / "snapshot" / source.name
    if target.exists() and sha256(target) != digest:
        target = target.with_name(f"{target.stem}-{digest[:8]}{target.suffix}")
    if not target.exists():
        shutil.copy2(source, target)

    manifest = {
        "schema_version": "2.0",
        "created_at": now(),
        "files": [{
            "original_path": str(source),
            "snapshot_path": target.relative_to(root).as_posix(),
            "name": source.name,
            "bytes": source.stat().st_size,
            "sha256": digest,
        }],
    }
    write_json(root / "00-source" / "source-manifest.json", manifest)
    for rel, payload in template_payloads().items():
        path = root / rel
        if not path.exists():
            write_json(path, payload)

    project = {
        "schema_version": "2.0",
        "framework": "FORGE x TRACE",
        "route": args.route,
        "created_at": now(),
        "updated_at": now(),
        "workspace": str(root),
        "phase_order": list(PHASES),
        "stale_from": "F",
    }
    write_json(root / "forge-project.json", project)
    log_event(root, "workspace_initialized", route=args.route, input=str(source), sha256=digest)
    print(f"Initialized FORGE workspace: {root}")
    print("Next: complete 01-forensics/asset-inventory.json and disposition-ledger.json")
    return 0


def load_required(root: Path, rel: str, errors: list[str]) -> dict:
    path = root / rel
    if not path.is_file():
        errors.append(f"missing: {rel}")
        return {}
    try:
        data = read_json(path)
    except Exception as exc:
        errors.append(f"invalid JSON: {rel}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"JSON object required: {rel}")
        return {}
    return data


def nonempty(data: dict, fields: tuple[str, ...], rel: str, errors: list[str]) -> None:
    for field in fields:
        value = data.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"{rel}: field '{field}' is empty")


def gate_f(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_required(root, "00-source/source-manifest.json", errors)
    files = manifest.get("files") or []
    if not files:
        errors.append("source manifest contains no files")
    for item in files:
        rel = item.get("snapshot_path", "")
        path = root / rel
        if not rel or not inside(root, path) or not path.is_file():
            errors.append(f"source snapshot missing or unsafe: {rel}")
        elif item.get("sha256") != sha256(path):
            errors.append(f"source snapshot hash mismatch: {rel}")

    inventory = load_required(root, "01-forensics/asset-inventory.json", errors)
    if inventory.get("complete") is not True:
        errors.append("asset inventory is not marked complete")
    assets = inventory.get("assets") or []
    ids: set[str] = set()
    for asset in assets:
        aid = asset.get("id")
        if not aid or aid in ids:
            errors.append(f"asset id missing or duplicated: {aid!r}")
        ids.add(aid)
        if not asset.get("type") or not asset.get("source_locator"):
            errors.append(f"asset {aid!r} needs type and source_locator")
    if not assets:
        errors.append("asset inventory is empty")

    ledger = load_required(root, "01-forensics/disposition-ledger.json", errors)
    if ledger.get("complete") is not True:
        errors.append("disposition ledger is not marked complete")
    entries = ledger.get("entries") or []
    covered: set[str] = set()
    for entry in entries:
        aid = entry.get("asset_id")
        action = entry.get("action")
        covered.add(aid)
        if action not in DISPOSITIONS:
            errors.append(f"asset {aid!r} has invalid disposition: {action!r}")
        if action == "pending":
            errors.append(f"asset {aid!r} still has pending disposition")
        if action == "drop" and (not entry.get("reason") or entry.get("author_approved") is not True):
            errors.append(f"dropped asset {aid!r} needs reason and author_approved=true")
    missing = sorted(ids - covered)
    if missing:
        errors.append(f"assets missing disposition: {', '.join(missing)}")
    extra = sorted(x for x in covered - ids if x)
    if extra:
        warnings.append(f"disposition entries without inventory asset: {', '.join(extra)}")
    return errors, warnings


def gate_o(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    position = load_required(root, "02-opportunity/research-positioning.json", errors)
    if position.get("complete") is not True:
        errors.append("research positioning is not marked complete")
    nonempty(position, ("problem", "gap", "approach", "evidence", "contribution", "boundary"),
             "research-positioning.json", errors)
    status = position.get("conversion_status")
    if status != "eligible":
        errors.append(f"conversion_status must be 'eligible' to pass O (got {status!r})")

    profile = load_required(root, "02-opportunity/model-profile.json", errors)
    if profile.get("complete") is not True:
        errors.append("model profile is not marked complete")
    primary = profile.get("primary_archetype")
    if primary not in ARCHETYPES:
        errors.append(f"invalid primary_archetype: {primary!r}")
    secondaries = profile.get("secondary_archetypes") or []
    invalid = sorted(set(secondaries) - ARCHETYPES)
    if invalid:
        errors.append(f"invalid secondary archetypes: {', '.join(invalid)}")
    nonempty(profile, ("assumptions", "risks"), "model-profile.json", errors)
    return errors, warnings


def gate_r(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    plan = load_required(root, "03-revalidation/validation-plan.json", errors)
    if plan.get("complete") is not True:
        errors.append("validation plan is not marked complete")
    claims = plan.get("claims") or []
    if not claims:
        errors.append("validation plan contains no claims")
    seen: set[str] = set()
    for claim in claims:
        cid = claim.get("claim_id")
        tests = claim.get("tests") or []
        if not cid or cid in seen:
            errors.append(f"validation claim id missing or duplicated: {cid!r}")
        seen.add(cid)
        minimum = 2 if claim.get("risk") == "high" else 1
        if len(tests) < minimum:
            errors.append(f"claim {cid!r} needs at least {minimum} validation route(s)")
        for test in tests:
            if not test.get("method") or not test.get("evidence_type"):
                errors.append(f"claim {cid!r} has a test without method/evidence_type")

    results = load_required(root, "03-revalidation/validation-results.json", errors)
    if results.get("complete") is not True:
        errors.append("validation results are not marked complete")
    baseline = results.get("baseline_status")
    if baseline not in {"compared", "not_applicable_with_reason"}:
        errors.append("baseline_status must be compared or not_applicable_with_reason")
    if baseline == "not_applicable_with_reason" and not results.get("baseline_reason"):
        errors.append("baseline_reason is required when baseline is not applicable")
    runs = results.get("runs") or []
    if not runs:
        errors.append("validation results contain no executed runs")
    for run in runs:
        if not run.get("run_id") or run.get("executed") is not True or not run.get("result_locator"):
            errors.append("each validation run needs run_id, executed=true and result_locator")
    blockers = results.get("unresolved_blockers") or []
    if blockers:
        errors.append(f"unresolved validation blockers: {len(blockers)}")
    return errors, warnings


def gate_g(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    claims = load_required(root, "04-manuscript/claim-map.json", errors)
    if claims.get("complete") is not True:
        errors.append("claim map is not marked complete")
    items = claims.get("claims") or []
    if not items:
        errors.append("claim map contains no claims")
    for item in items:
        claim_id = item.get("claim_id")
        if not item.get("claim_id") or not item.get("text") or not item.get("evidence_ids"):
            errors.append("every claim needs claim_id, text and evidence_ids")
        if item.get("risk") == "high" and item.get("status") != "SUPPORTED":
            errors.append(f"high-risk claim {claim_id!r} is not SUPPORTED")
        elif item.get("status") in {"UNSUPPORTED", "CONTRADICTED", "PENDING", None}:
            errors.append(f"claim {claim_id!r} has blocking status {item.get('status')!r}")

        verification = item.get("verification")
        if not isinstance(verification, dict):
            errors.append(
                f"claim {claim_id!r} verification needs required_depth, reached_depth, "
                "checked_at and evidence_locator"
            )
            continue
        required = verification.get("required_depth")
        reached = verification.get("reached_depth")
        if required not in VERIFICATION_RANK:
            errors.append(f"claim {claim_id!r} has invalid verification required_depth {required!r}")
        elif VERIFICATION_RANK[required] < VERIFICATION_RANK[MIN_GATE_G_VERIFICATION]:
            errors.append(
                f"claim {claim_id!r} verification required_depth {required!r} is below "
                f"Gate G minimum {MIN_GATE_G_VERIFICATION!r}"
            )
        if reached not in VERIFICATION_RANK:
            errors.append(f"claim {claim_id!r} has invalid verification reached_depth {reached!r}")
        if (required in VERIFICATION_RANK and reached in VERIFICATION_RANK
                and VERIFICATION_RANK[reached] < VERIFICATION_RANK[required]):
            errors.append(
                f"claim {claim_id!r} verification reached_depth {reached!r} is below "
                f"required_depth {required!r}"
            )
        if not verification.get("checked_at") or not verification.get("evidence_locator"):
            errors.append(
                f"claim {claim_id!r} verification needs checked_at and evidence_locator"
            )

    figures = load_required(root, "04-manuscript/figure-manifest.json", errors)
    if figures.get("complete") is not True:
        errors.append("figure manifest is not marked complete")
    figure_items = figures.get("figures") or []
    if not figure_items and not figures.get("waiver_reason"):
        errors.append("no figures declared and no waiver_reason supplied")
    for fig in figure_items:
        if not fig.get("figure_id") or not fig.get("claim_ids") or not fig.get("source_data"):
            errors.append("each figure needs figure_id, claim_ids and source_data")
        check_editable_artifact(root, fig, errors, warnings)
        review = fig.get("visual_review") or {}
        if not isinstance(review, dict):
            errors.append(f"figure {fig.get('figure_id')!r} visual_review must be an object")
            review = {}
        if not review.get("reviewer") or not review.get("reviewed_at"):
            errors.append(f"figure {fig.get('figure_id')!r} lacks signed visual_review")
        target_width = fig.get("target_width_mm")
        reviewed_width = review.get("reviewed_width_mm")
        if not is_positive_number(target_width):
            errors.append(
                f"figure {fig.get('figure_id')!r} needs a positive target_width_mm"
            )
        if not is_positive_number(reviewed_width):
            errors.append(
                f"figure {fig.get('figure_id')!r} visual_review needs a positive "
                "reviewed_width_mm"
            )
        elif (is_positive_number(target_width)
              and abs(float(reviewed_width) - float(target_width)) > FINAL_SIZE_TOLERANCE_MM):
            errors.append(
                f"figure {fig.get('figure_id')!r} reviewed_width_mm={reviewed_width} does not "
                f"match target_width_mm={target_width} within {FINAL_SIZE_TOLERANCE_MM} mm"
            )
        outputs = fig.get("outputs") or []
        if not isinstance(outputs, list) or not outputs:
            errors.append(f"figure {fig.get('figure_id')!r} needs current output files")
            outputs = []
        output_hashes = review.get("output_sha256")
        if not isinstance(output_hashes, dict):
            errors.append(
                f"figure {fig.get('figure_id')!r} visual_review needs output_sha256 bindings"
            )
            output_hashes = {}
        declared_outputs: set[str] = set()
        for rel in outputs:
            if not isinstance(rel, str) or not rel.strip():
                errors.append(f"figure {fig.get('figure_id')!r} has an invalid output path")
                continue
            declared_outputs.add(rel)
            path = root / rel
            if not inside(root, path) or not path.is_file():
                errors.append(f"figure {fig.get('figure_id')!r} output missing or unsafe: {rel}")
                continue
            expected = output_hashes.get(rel)
            if not is_sha256(expected):
                errors.append(
                    f"figure {fig.get('figure_id')!r} output {rel!r} lacks a lowercase SHA-256 "
                    "from the visual review"
                )
            elif expected != sha256(path):
                errors.append(
                    f"figure {fig.get('figure_id')!r} output {rel!r} changed after visual review"
                )
        extras = sorted(str(key) for key in output_hashes if key not in declared_outputs)
        if extras:
            warnings.append(
                f"figure {fig.get('figure_id')!r} visual_review has hashes for undeclared outputs: "
                + ", ".join(extras)
            )

    citations = load_required(root, "04-manuscript/citation-audit.json", errors)
    if citations.get("complete") is not True:
        errors.append("citation audit is not marked complete")
    if citations.get("blockers"):
        errors.append(f"citation audit declares {len(citations.get('blockers'))} blocker(s)")
    citation_items = citations.get("citations") or []
    if not citation_items:
        errors.append("citation audit contains no citation records")
    for cite in citation_items:
        cid = cite.get("citation_id")
        if cite.get("identity_status") != "VERIFIED":
            errors.append(f"citation {cid!r} identity is not VERIFIED")
        check_publication_integrity(cite, cid, errors)
        support = cite.get("support_status")
        if support in {"CONTRADICTS", "DOES_NOT_SUPPORT"}:
            errors.append(f"citation {cid!r} has blocking support status {support}")
        if support == "PARTIALLY_SUPPORTS" and cite.get("claim_adjusted") is not True:
            errors.append(f"citation {cid!r} is PARTIALLY_SUPPORTS but claim_adjusted is not true")
        if support == "BACKGROUND_ONLY" and cite.get("sentence_tier") != "background":
            errors.append(f"citation {cid!r} is BACKGROUND_ONLY for a non-background sentence")
        if support == "CANNOT_VERIFY":
            errors.append(f"citation {cid!r} cannot be verified")
        tier = cite.get("sentence_tier") or "causal"
        access = cite.get("access_level")
        if tier not in MIN_ACCESS:
            errors.append(f"citation {cid!r} has invalid sentence_tier {tier!r}")
        elif access not in ACCESS_RANK or ACCESS_RANK[access] < MIN_ACCESS[tier]:
            errors.append(f"citation {cid!r} access_level {access!r} is too shallow for {tier}")
        if tier in {"quantitative", "causal", "mechanistic"} and not cite.get("locator"):
            errors.append(f"citation {cid!r} needs a page/figure/table locator for {tier}")

    if not any((root / "04-manuscript" / name).is_file() for name in MANUSCRIPT_NAMES):
        errors.append("missing manuscript.md, manuscript.tex or manuscript.docx")
    return errors, warnings


def gate_e(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    journal = load_required(root, "05-editorial/journal-evidence.json", errors)
    if journal.get("complete") is not True:
        errors.append("journal evidence is not marked complete")
    selected = journal.get("selected_journal")
    candidates = journal.get("candidates") or []
    match = next((x for x in candidates if x.get("name") == selected), None)
    if not selected or match is None:
        errors.append("selected_journal must match a candidate")
    elif not match.get("official_scope_url") or not match.get("retrieved_at"):
        errors.append("selected journal needs official_scope_url and retrieved_at")

    panel = load_required(root, "05-editorial/reviewer-panel.json", errors)
    if panel.get("complete") is not True:
        errors.append("reviewer panel is not marked complete")
    reviewers = panel.get("reviewers") or []
    if not 3 <= len(reviewers) <= 5:
        errors.append("reviewer panel must contain 3-5 reviewers")
    roles = [x.get("role") for x in reviewers]
    if len(set(roles)) != len(roles) or any(not x for x in roles):
        errors.append("reviewer roles must be non-empty and distinct")
    verdict = panel.get("verdict")
    if verdict != READY:
        errors.append(f"reviewer panel verdict is not {READY}: {verdict!r}")
    if "acceptance_probability" in panel:
        errors.append("reviewer panel must not estimate acceptance_probability")

    preflight = load_required(root, "05-editorial/submission-preflight.json", errors)
    if preflight.get("complete") is not True:
        errors.append("submission preflight is not marked complete")
    if preflight.get("status") != READY:
        errors.append(f"submission preflight status is not {READY}")
    if preflight.get("blockers"):
        errors.append(f"submission preflight contains {len(preflight.get('blockers'))} blocker(s)")
    return errors, warnings


GATE_FUNCS = {"F": gate_f, "O": gate_o, "R": gate_r, "G": gate_g, "E": gate_e}


def evaluate(root: Path, phase: str) -> dict:
    if not (root / "forge-project.json").is_file():
        return {"phase": phase, "name": PHASE_NAMES[phase], "passed": False,
                "errors": ["forge-project.json missing; run init first"], "warnings": []}
    errors, warnings = GATE_FUNCS[phase](root)
    return {"phase": phase, "name": PHASE_NAMES[phase], "passed": not errors,
            "checked_at": now(), "errors": errors, "warnings": warnings,
            "scope": "deterministic contract only; scientific semantics require Agent/author review"}


def print_result(result: dict) -> None:
    marker = "PASS" if result["passed"] else "BLOCKED"
    print(f"[{result['phase']}] {marker} - {result['name']}")
    for item in result.get("errors", []):
        print(f"  ERROR: {item}")
    for item in result.get("warnings", []):
        print(f"  WARN: {item}")


def command_gate(args: argparse.Namespace) -> int:
    root = Path(args.workspace).expanduser().resolve()
    project_path = root / "forge-project.json"
    project = read_json(project_path) if project_path.is_file() else {}
    stale = project.get("stale_from") if isinstance(project, dict) else None
    if stale in PHASES and PHASES.index(args.phase) > PHASES.index(stale):
        result = {"phase": args.phase, "name": PHASE_NAMES[args.phase], "passed": False,
                  "checked_at": now(), "warnings": [],
                  "errors": [f"phase {stale} is stale and must pass before {args.phase}"]}
    else:
        result = evaluate(root, args.phase)
    if result["passed"] and isinstance(project, dict) and stale == args.phase:
        index = PHASES.index(args.phase)
        project["stale_from"] = PHASES[index + 1] if index + 1 < len(PHASES) else None
        project["updated_at"] = now()
        write_json(project_path, project)
    write_json(root / "audit" / f"gate-{args.phase.lower()}.json", result)
    log_event(root, "gate_checked", phase=args.phase, passed=result["passed"],
              errors=len(result["errors"]), warnings=len(result["warnings"]))
    print_result(result)
    return 0 if result["passed"] else 2


def command_status(args: argparse.Namespace) -> int:
    root = Path(args.workspace).expanduser().resolve()
    if not (root / "forge-project.json").is_file():
        print("ERROR forge-project.json missing; run init first", file=sys.stderr)
        return 2
    project = read_json(root / "forge-project.json")
    stale = project.get("stale_from") if isinstance(project, dict) else None
    results = [evaluate(root, phase) for phase in PHASES]
    if stale in PHASES:
        stale_index = PHASES.index(stale)
        for index, result in enumerate(results):
            if index >= stale_index:
                result["passed"] = False
                result["errors"] = [*result["errors"], f"phase is stale from {stale}; rerun gates in order"]
    for result in results:
        print_result(result)
    first_blocked = next((x["phase"] for x in results if not x["passed"]), None)
    summary = {
        "checked_at": now(),
        "phases": results,
        "next_phase": first_blocked,
        "status": READY if first_blocked is None else "AUTHOR_ACTION_REQUIRED",
    }
    write_json(root / "audit" / "forge-status.json", summary)
    print(f"Overall: {summary['status']}; next_phase={first_blocked or 'none'}")
    return 0


def changed_phase(value: str) -> str | None:
    normalized = value.replace("\\", "/").lstrip("./")
    top = normalized.split("/", 1)[0]
    return PREFIX_PHASE.get(top)


def command_impact(args: argparse.Namespace) -> int:
    root = Path(args.workspace).expanduser().resolve()
    if not (root / "forge-project.json").is_file():
        print("ERROR forge-project.json missing; run init first", file=sys.stderr)
        return 2
    mapped = [(item, changed_phase(item)) for item in args.changed]
    known = [phase for _, phase in mapped if phase]
    if not known:
        print("ERROR none of the changed paths map to a FORGE phase", file=sys.stderr)
        return 2
    earliest = min(known, key=PHASES.index)
    affected = list(PHASES[PHASES.index(earliest):])
    report = {
        "schema_version": "2.0",
        "analyzed_at": now(),
        "changed": [{"path": path, "phase": phase or "unknown"} for path, phase in mapped],
        "earliest_affected_phase": earliest,
        "affected_phases": affected,
        "unknown_paths": [path for path, phase in mapped if phase is None],
        "actions": {
            "F": "rebuild source inventory, dispositions and all downstream artifacts",
            "O": "reconfirm research positioning and rerun all downstream work",
            "R": "rerun validation, then rebuild claims, figures and editorial checks",
            "G": "rebuild manuscript-linked claims, figures, citations and editorial checks",
            "E": "refresh journal evidence, reviews and submission package",
        },
        "limit": "Artifact-level propagation only; semantic impact still requires human review.",
    }
    write_json(root / "audit" / "impact-report.json", report)
    project = read_json(root / "forge-project.json")
    if isinstance(project, dict):
        old = project.get("stale_from")
        if old in PHASES:
            earliest = min((old, earliest), key=PHASES.index)
        project["stale_from"] = earliest
        project["updated_at"] = now()
        write_json(root / "forge-project.json", project)
    log_event(root, "impact_analyzed", earliest=earliest, affected=affected, changed=args.changed)
    print(f"Earliest affected phase: {earliest}")
    print(f"Affected phases: {', '.join(affected)}")
    for path in report["unknown_paths"]:
        print(f"WARN unmapped path: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FORGE x TRACE workspace utility")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="initialize a traceable FORGE workspace")
    p_init.add_argument("workspace")
    p_init.add_argument("--input", required=True)
    p_init.add_argument("--route", choices=("diagnose", "full", "revalidation", "journal", "revision"),
                        default="full")
    p_init.set_defaults(func=command_init)

    p_status = sub.add_parser("status", help="show deterministic phase contract status")
    p_status.add_argument("workspace")
    p_status.set_defaults(func=command_status)

    p_gate = sub.add_parser("gate", help="check one deterministic phase contract")
    p_gate.add_argument("workspace")
    p_gate.add_argument("phase", choices=PHASES)
    p_gate.set_defaults(func=command_gate)

    p_impact = sub.add_parser("impact", help="propagate changed artifact paths to downstream phases")
    p_impact.add_argument("workspace")
    p_impact.add_argument("--changed", nargs="+", required=True)
    p_impact.set_defaults(func=command_impact)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
