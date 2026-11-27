#!/usr/bin/env python3
"""Compile an evidence-bounded target-journal writing profile.

The input contains paraphrased structural/rhetorical observations, never paper
text. Only training papers contribute rules. A held-out author group and a
profile-bound human evaluation are required before the profile is labelled
usable. This tool validates the declared contract; it does not judge scientific
quality or turn observed patterns into journal requirements.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.journal_fit import normalize_issn  # noqa: E402
from readiness.utils import load_json, save_json  # noqa: E402


DIMENSIONS = {
    "problem_framing",
    "article_structure",
    "model_description",
    "validation_reporting",
    "result_interpretation",
    "limitations",
}
ACCESS_BASES = {
    "open_access",
    "author_supplied",
    "institutional_access",
    "publisher_access",
    "other_legal_access",
}
FORBIDDEN_VERBATIM_FIELDS = {
    "abstract",
    "excerpt",
    "full_text",
    "quote",
    "sentence_text",
    "verbatim",
}
EVALUATION_CHECKS = {
    "scientific_content_preserved",
    "numbers_units_formulas_preserved",
    "citations_preserved",
    "structure_fit_improved_or_neutral",
    "no_verbatim_mimicry",
}
PATTERN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*$")
SHA256_RE = re.compile(r"[a-f0-9]{64}$")
DOI_RE = re.compile(r"10\.\d{4,9}/\S+$", re.IGNORECASE)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return " ".join(value.split())


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _reject_verbatim_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in FORBIDDEN_VERBATIM_FIELDS:
                raise ValueError(f"forbidden verbatim field at {path}.{key}")
            _reject_verbatim_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_verbatim_fields(item, f"{path}[{index}]")


def _validate_timestamp(value: Any, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return text


def _profile_fingerprint(core: dict) -> str:
    payload = json.dumps(
        core, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _evaluation_result(evaluation: dict, fingerprint: str,
                       heldout_ids: list[str]) -> tuple[str, dict]:
    _reject_verbatim_fields(evaluation, "evaluation")
    if evaluation.get("profile_fingerprint") != fingerprint:
        raise ValueError("held-out evaluation fingerprint does not match this profile")
    supplied_ids = evaluation.get("heldout_ids")
    if not isinstance(supplied_ids, list) or sorted(supplied_ids) != heldout_ids:
        raise ValueError("held-out evaluation must cover the exact heldout_ids")
    reviewer = _text(evaluation.get("reviewed_by"), "evaluation.reviewed_by")
    reviewed_at = _validate_timestamp(
        evaluation.get("reviewed_at"), "evaluation.reviewed_at"
    )
    decision = evaluation.get("decision")
    if decision not in {"accept", "revise", "reject"}:
        raise ValueError("evaluation.decision must be accept, revise, or reject")
    checks = evaluation.get("checks")
    if not isinstance(checks, dict) or set(checks) != EVALUATION_CHECKS:
        raise ValueError("evaluation.checks must contain the complete check set")
    if any(not isinstance(value, bool) for value in checks.values()):
        raise ValueError("evaluation check values must be boolean")
    failures = evaluation.get("failures")
    if not isinstance(failures, list) or any(not isinstance(x, str) for x in failures):
        raise ValueError("evaluation.failures must be a list of strings")

    accepted = decision == "accept" and all(checks.values()) and not failures
    status = (
        "USABLE_WITH_RECORDED_HUMAN_APPROVAL"
        if accepted
        else "REVISION_REQUIRED_AFTER_HELDOUT_EVALUATION"
    )
    return status, {
        "contract_valid": True,
        "profile_fingerprint": fingerprint,
        "heldout_ids": heldout_ids,
        "reviewed_by": reviewer,
        "reviewed_at": reviewed_at,
        "decision": decision,
        "checks": checks,
        "failures": failures,
        "important_limit": (
            "The tool validates the recorded review contract, not the truth or "
            "quality of the human judgment."
        ),
    }


def compile_profile(cards: dict, policy: dict,
                    *, evaluation: dict | None = None) -> dict:
    """Validate cards and compile repeated train-corpus observations."""
    if not isinstance(cards, dict) or cards.get("schema_version") != "1.0":
        raise ValueError("cards schema_version must be 1.0")
    _reject_verbatim_fields(cards, "cards")

    journal = cards.get("journal")
    if not isinstance(journal, dict):
        raise ValueError("journal must be an object")
    journal_name = _text(journal.get("name"), "journal.name")
    issn = normalize_issn(str(journal.get("issn") or ""))
    if not issn:
        raise ValueError("journal.issn must be a valid ISSN")
    article_type = _text(cards.get("article_type"), "article_type")

    if not isinstance(policy, dict):
        raise ValueError("policy must be an object")
    required_policy = {
        "min_train_papers",
        "min_train_author_groups",
        "min_pattern_author_groups",
    }
    if set(policy) != required_policy:
        raise ValueError("policy must contain only the three explicit minimums")
    minimums = {key: _positive_int(policy[key], f"policy.{key}")
                for key in sorted(required_policy)}

    papers = cards.get("papers")
    if not isinstance(papers, list) or not papers:
        raise ValueError("papers must be a non-empty list")

    ids: set[str] = set()
    dois: set[str] = set()
    hashes: set[str] = set()
    train: list[dict] = []
    heldout: list[dict] = []
    source_registry: list[dict] = []
    groups_by_split = {"train": set(), "heldout": set()}

    for index, paper in enumerate(papers):
        prefix = f"papers[{index}]"
        if not isinstance(paper, dict):
            raise ValueError(f"{prefix} must be an object")
        paper_id = _text(paper.get("id"), f"{prefix}.id")
        if paper_id in ids:
            raise ValueError(f"duplicate paper id: {paper_id}")
        ids.add(paper_id)
        doi = _text(paper.get("doi"), f"{prefix}.doi")
        doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi,
                     flags=re.IGNORECASE).lower()
        if not DOI_RE.fullmatch(doi):
            raise ValueError(f"{prefix}.doi must be a valid DOI")
        if doi in dois:
            raise ValueError(f"duplicate paper DOI: {doi}")
        dois.add(doi)
        digest = str(paper.get("file_sha256") or "").lower()
        if not SHA256_RE.fullmatch(digest):
            raise ValueError(f"{prefix}.file_sha256 must be a lowercase SHA-256")
        if digest in hashes:
            raise ValueError(f"duplicate paper file hash: {digest}")
        hashes.add(digest)
        source_url = _text(paper.get("source_url"), f"{prefix}.source_url")
        if not source_url.startswith(("https://", "http://")):
            raise ValueError(f"{prefix}.source_url must be HTTP(S)")
        if paper.get("access_basis") not in ACCESS_BASES:
            raise ValueError(f"{prefix}.access_basis is not recognized")
        if not isinstance(paper.get("redistribution_allowed"), bool):
            raise ValueError(f"{prefix}.redistribution_allowed must be boolean")
        for field in ("metadata_verified", "full_text_read", "visual_checked"):
            if paper.get(field) is not True:
                raise ValueError(f"{prefix}.{field} must be true")
        author_group = _text(paper.get("author_group"), f"{prefix}.author_group")
        split = paper.get("split")
        if split not in groups_by_split:
            raise ValueError(f"{prefix}.split must be train or heldout")
        groups_by_split[split].add(author_group)
        observations = paper.get("observations", [])
        if not isinstance(observations, list):
            raise ValueError(f"{prefix}.observations must be a list")
        normalized = dict(paper, id=paper_id, file_sha256=digest,
                          doi=doi, source_url=source_url, author_group=author_group,
                          observations=observations)
        source_registry.append(
            {
                "id": paper_id,
                "doi": doi,
                "source_url": source_url,
                "access_basis": paper["access_basis"],
                "redistribution_allowed": paper["redistribution_allowed"],
                "file_sha256": digest,
                "author_group": author_group,
                "split": split,
                "metadata_verified": True,
                "full_text_read": True,
                "visual_checked": True,
            }
        )
        if split == "heldout":
            if observations:
                raise ValueError("held-out papers must not supply observations")
            heldout.append(normalized)
        else:
            if not observations:
                raise ValueError(f"{prefix} train paper needs observations")
            train.append(normalized)

    overlap = groups_by_split["train"] & groups_by_split["heldout"]
    if overlap:
        raise ValueError(f"author-group leakage across train/heldout: {sorted(overlap)}")
    if not heldout:
        raise ValueError("at least one held-out author group is required")
    if len(train) < minimums["min_train_papers"]:
        raise ValueError("training paper count is below project policy")
    if len(groups_by_split["train"]) < minimums["min_train_author_groups"]:
        raise ValueError("training author-group count is below project policy")

    aggregated: dict[str, dict] = {}
    for paper in train:
        seen_in_paper: set[str] = set()
        for index, observation in enumerate(paper["observations"]):
            if not isinstance(observation, dict):
                raise ValueError(f"{paper['id']} observation {index} must be an object")
            pattern_id = _text(observation.get("pattern_id"), "pattern_id")
            if not PATTERN_ID_RE.fullmatch(pattern_id):
                raise ValueError(f"invalid pattern_id: {pattern_id}")
            if pattern_id in seen_in_paper:
                raise ValueError(f"duplicate pattern_id in {paper['id']}: {pattern_id}")
            seen_in_paper.add(pattern_id)
            dimension = observation.get("dimension")
            if dimension not in DIMENSIONS:
                raise ValueError(f"unsupported observation dimension: {dimension}")
            definition = _text(observation.get("definition"), "definition")
            locator = _text(observation.get("locator"), "locator")
            row = aggregated.setdefault(
                pattern_id,
                {
                    "pattern_id": pattern_id,
                    "dimension": dimension,
                    "definition": definition,
                    "paper_ids": set(),
                    "author_groups": set(),
                    "evidence": [],
                },
            )
            if row["dimension"] != dimension or row["definition"] != definition:
                raise ValueError(f"conflicting definition for pattern_id {pattern_id}")
            row["paper_ids"].add(paper["id"])
            row["author_groups"].add(paper["author_group"])
            row["evidence"].append(
                {
                    "paper_id": paper["id"],
                    "doi": paper["doi"],
                    "source_url": paper["source_url"],
                    "locator": locator,
                }
            )

    rules = []
    excluded = []
    minimum_support = minimums["min_pattern_author_groups"]
    for pattern_id, row in sorted(aggregated.items()):
        support_groups = len(row["author_groups"])
        if support_groups < minimum_support:
            excluded.append(
                {
                    "pattern_id": pattern_id,
                    "reason": (
                        f"support_author_groups={support_groups} below project "
                        f"policy {minimum_support}"
                    ),
                }
            )
            continue
        rules.append(
            {
                "pattern_id": pattern_id,
                "dimension": row["dimension"],
                "definition": row["definition"],
                "support_papers": len(row["paper_ids"]),
                "support_author_groups": support_groups,
                "evidence": sorted(row["evidence"], key=lambda x: x["paper_id"]),
            }
        )
    if not rules:
        raise ValueError("no observed pattern meets the project support policy")

    heldout_ids = sorted(paper["id"] for paper in heldout)
    core = {
        "journal": {"name": journal_name, "issn": issn},
        "article_type": article_type,
        "policy": minimums,
        "source_registry": sorted(source_registry, key=lambda x: x["id"]),
        "training_ids": sorted(paper["id"] for paper in train),
        "heldout_ids": heldout_ids,
        "rules": rules,
    }
    fingerprint = _profile_fingerprint(core)
    profile_status = "DRAFT_NEEDS_HELDOUT_EVALUATION"
    heldout_evaluation = None
    if evaluation is not None:
        if not isinstance(evaluation, dict):
            raise ValueError("evaluation must be an object")
        profile_status, heldout_evaluation = _evaluation_result(
            evaluation, fingerprint, heldout_ids
        )

    return {
        "schema_version": "1.0",
        "source_class": "observed_pattern",
        **core,
        "profile_fingerprint": fingerprint,
        "profile_status": profile_status,
        "excluded_patterns": excluded,
        "heldout_evaluation": heldout_evaluation,
        "important_limits": [
            "Observed writing patterns are not official journal requirements.",
            "The profile may guide structure and rhetoric only; it cannot change facts, "
            "numbers, units, formulas, citations, evidence strength, or model results.",
            "The input contract rejects verbatim-content fields; a human must still "
            "confirm that definitions are independently paraphrased.",
            "A usable profile does not establish journal fit, submission readiness, or "
            "acceptance probability.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile a held-out, evidence-bounded target-journal style profile."
    )
    parser.add_argument("--cards", required=True, help="JSON corpus-card file")
    parser.add_argument("--min-train-papers", required=True, type=int)
    parser.add_argument("--min-train-author-groups", required=True, type=int)
    parser.add_argument("--min-pattern-author-groups", required=True, type=int)
    parser.add_argument("--evaluation", help="optional human held-out evaluation JSON")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    policy = {
        "min_train_papers": args.min_train_papers,
        "min_train_author_groups": args.min_train_author_groups,
        "min_pattern_author_groups": args.min_pattern_author_groups,
    }
    try:
        result = compile_profile(
            load_json(args.cards),
            policy,
            evaluation=load_json(args.evaluation) if args.evaluation else None,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"journal style profile: BLOCKED - {exc}", file=sys.stderr)
        return 2
    save_json(args.out, result)
    print(
        f"profile={result['profile_status']} rules={len(result['rules'])} "
        f"fingerprint={result['profile_fingerprint']} -> {args.out}"
    )
    return 0 if result["profile_status"] == "USABLE_WITH_RECORDED_HUMAN_APPROVAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
