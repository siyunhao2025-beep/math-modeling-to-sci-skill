from __future__ import annotations

import json
import sys

import pytest

from readiness import journal_style_profile


def _cards() -> dict:
    return {
        "schema_version": "1.0",
        "journal": {"name": "Synthetic Journal", "issn": "2045-2322"},
        "article_type": "Research Article",
        "papers": [
            {
                "id": "train-a",
                "doi": "10.1000/train-a",
                "source_url": "https://example.org/train-a",
                "access_basis": "open_access",
                "redistribution_allowed": False,
                "file_sha256": "a" * 64,
                "author_group": "group-a",
                "split": "train",
                "metadata_verified": True,
                "full_text_read": True,
                "visual_checked": True,
                "observations": [
                    {
                        "pattern_id": "validation-before-interpretation",
                        "dimension": "validation_reporting",
                        "definition": "Report the validation result before interpreting its implication.",
                        "locator": "p. 4, Results, paragraph 2",
                    },
                    {
                        "pattern_id": "single-team-pattern",
                        "dimension": "article_structure",
                        "definition": "Place the sensitivity analysis after the main result.",
                        "locator": "p. 5, heading 3.2",
                    },
                ],
            },
            {
                "id": "train-b",
                "doi": "10.1000/train-b",
                "source_url": "https://example.org/train-b",
                "access_basis": "author_supplied",
                "redistribution_allowed": False,
                "file_sha256": "b" * 64,
                "author_group": "group-b",
                "split": "train",
                "metadata_verified": True,
                "full_text_read": True,
                "visual_checked": True,
                "observations": [
                    {
                        "pattern_id": "validation-before-interpretation",
                        "dimension": "validation_reporting",
                        "definition": "Report the validation result before interpreting its implication.",
                        "locator": "p. 6, Results, paragraph 1",
                    }
                ],
            },
            {
                "id": "heldout-c",
                "doi": "10.1000/heldout-c",
                "source_url": "https://example.org/heldout-c",
                "access_basis": "institutional_access",
                "redistribution_allowed": False,
                "file_sha256": "c" * 64,
                "author_group": "group-c",
                "split": "heldout",
                "metadata_verified": True,
                "full_text_read": True,
                "visual_checked": True,
                "observations": [],
            },
        ],
    }


def _policy() -> dict:
    return {
        "min_train_papers": 2,
        "min_train_author_groups": 2,
        "min_pattern_author_groups": 2,
    }


def test_profile_uses_train_only_and_keeps_low_support_visible():
    result = journal_style_profile.compile_profile(_cards(), _policy())

    assert result["source_class"] == "observed_pattern"
    assert result["profile_status"] == "DRAFT_NEEDS_HELDOUT_EVALUATION"
    assert [rule["pattern_id"] for rule in result["rules"]] == [
        "validation-before-interpretation"
    ]
    assert result["rules"][0]["support_author_groups"] == 2
    assert result["heldout_ids"] == ["heldout-c"]
    assert result["source_registry"][0]["doi"] == "10.1000/heldout-c"
    assert result["source_registry"][0]["file_sha256"] == "c" * 64
    assert result["excluded_patterns"] == [
        {
            "pattern_id": "single-team-pattern",
            "reason": "support_author_groups=1 below project policy 2",
        }
    ]
    changed_cards = _cards()
    changed_cards["papers"][0]["file_sha256"] = "d" * 64
    changed = journal_style_profile.compile_profile(changed_cards, _policy())
    assert changed["profile_fingerprint"] != result["profile_fingerprint"]


def test_author_group_leakage_is_rejected():
    cards = _cards()
    cards["papers"][2]["author_group"] = "group-a"

    with pytest.raises(ValueError, match="author-group leakage"):
        journal_style_profile.compile_profile(cards, _policy())


def test_conflicting_pattern_definitions_are_not_silently_merged():
    cards = _cards()
    cards["papers"][1]["observations"][0]["definition"] = (
        "Interpret the implication before reporting validation."
    )

    with pytest.raises(ValueError, match="conflicting definition"):
        journal_style_profile.compile_profile(cards, _policy())


def test_verbatim_payload_and_heldout_observations_are_rejected():
    cards = _cards()
    cards["papers"][0]["observations"][0]["quote"] = "copied sentence"
    with pytest.raises(ValueError, match="forbidden verbatim field"):
        journal_style_profile.compile_profile(cards, _policy())

    cards = _cards()
    cards["papers"][2]["observations"] = [
        {
            "pattern_id": "leaked-pattern",
            "dimension": "article_structure",
            "definition": "A held-out paper must not influence rule extraction.",
            "locator": "p. 2",
        }
    ]
    with pytest.raises(ValueError, match="held-out papers must not supply observations"):
        journal_style_profile.compile_profile(cards, _policy())


def test_human_heldout_approval_is_bound_to_the_compiled_profile():
    draft = journal_style_profile.compile_profile(_cards(), _policy())
    evaluation = {
        "profile_fingerprint": draft["profile_fingerprint"],
        "heldout_ids": ["heldout-c"],
        "reviewed_by": "author-or-editor",
        "reviewed_at": "2026-09-29T12:00:00+08:00",
        "decision": "accept",
        "checks": {
            "scientific_content_preserved": True,
            "numbers_units_formulas_preserved": True,
            "citations_preserved": True,
            "structure_fit_improved_or_neutral": True,
            "no_verbatim_mimicry": True,
        },
        "failures": [],
    }

    accepted = journal_style_profile.compile_profile(
        _cards(), _policy(), evaluation=evaluation
    )
    assert accepted["profile_status"] == "USABLE_WITH_RECORDED_HUMAN_APPROVAL"
    assert accepted["heldout_evaluation"]["contract_valid"] is True

    evaluation["profile_fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="fingerprint"):
        journal_style_profile.compile_profile(
            _cards(), _policy(), evaluation=evaluation
        )


def test_cli_writes_draft_but_returns_nonzero_until_human_evaluation(
    tmp_path, monkeypatch
):
    cards_path = tmp_path / "cards.json"
    out_path = tmp_path / "profile.json"
    cards_path.write_text(json.dumps(_cards()), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "journal_style_profile.py",
            "--cards",
            str(cards_path),
            "--min-train-papers",
            "2",
            "--min-train-author-groups",
            "2",
            "--min-pattern-author-groups",
            "2",
            "--out",
            str(out_path),
        ],
    )

    assert journal_style_profile.main() == 2
    draft = json.loads(out_path.read_text(encoding="utf-8"))
    assert draft["profile_status"] == "DRAFT_NEEDS_HELDOUT_EVALUATION"
