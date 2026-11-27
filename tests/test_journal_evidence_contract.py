from __future__ import annotations

from datetime import datetime, timezone
import json

from readiness import journal_fit
from readiness.pipeline_bridge import resolve_inputs


def test_issn_identity_is_normalized_and_check_digit_validated():
    assert journal_fit.normalize_issn("2045-2322") == "2045-2322"
    assert journal_fit.normalize_issn("20452322") == "2045-2322"
    assert journal_fit.normalize_issn("2045-2323") is None
    assert journal_fit.normalize_issn("2045junk2322") is None


def test_official_evidence_freshness_is_explicit_and_policy_bound():
    now = datetime(2026, 9, 28, tzinfo=timezone.utc)
    assert journal_fit.evidence_freshness(None, 30, now=now)["status"] == "UNVERIFIED"
    assert (
        journal_fit.evidence_freshness("2026-09-20T00:00:00Z", None, now=now)["status"]
        == "POLICY_UNSET"
    )
    assert (
        journal_fit.evidence_freshness("2026-09-20T00:00:00Z", 30, now=now)["status"]
        == "CURRENT"
    )
    assert (
        journal_fit.evidence_freshness("2026-07-01T00:00:00Z", 30, now=now)["status"]
        == "STALE"
    )


def test_observed_articles_cannot_replace_current_official_requirements(tmp_path):
    manuscript = tmp_path / "manuscript.txt"
    scope = tmp_path / "scope.txt"
    article_types = tmp_path / "article-types.txt"
    recent = tmp_path / "recent.json"
    out = tmp_path / "fit.json"
    manuscript.write_text(
        "A reproducible optimization model for transport planning.", encoding="utf-8"
    )
    scope.write_text("Optimization models and transport planning.", encoding="utf-8")
    article_types.write_text("research article\n", encoding="utf-8")
    recent.write_text(
        '[{"title":"A related optimization article","abstract":"transport planning"}]',
        encoding="utf-8",
    )

    result = journal_fit.run(
        str(manuscript),
        "Synthetic Journal",
        "2045-2322",
        str(scope),
        str(out),
        article_types_file=str(article_types),
        article_type="research article",
        scope_source_url="https://example.org/scope",
        article_type_source_url="https://example.org/types",
        evidence_checked_at="2026-07-01T00:00:00Z",
        max_evidence_age_days=30,
        recent_cache=str(recent),
        now=datetime(2026, 9, 28, tzinfo=timezone.utc),
    )

    assert result["journal_identity"]["key"] == "issn:2045-2322"
    assert result["official_evidence"]["source_class"] == "official_requirement"
    assert result["official_evidence"]["freshness"]["status"] == "STALE"
    assert result["recent_corpus"]["source_class"] == "observed_pattern"
    assert any("stale" in blocker.lower() for blocker in result["blockers"])
    assert not result["ready_for_agent_semantic_review"]


def test_readiness_bridge_routes_explicit_freshness_metadata(tmp_path):
    evidence_dir = tmp_path / "04-journals" / "journal-evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "target-journal.json").write_text(
        json.dumps(
            {
                "journal_name": "Synthetic Journal",
                "issn": "2045-2322",
                "checked_at": "2026-09-28T00:00:00Z",
                "max_evidence_age_days": 21,
            }
        ),
        encoding="utf-8",
    )

    resolved = resolve_inputs(str(tmp_path))

    assert resolved["evidence_checked_at"] == "2026-09-28T00:00:00Z"
    assert resolved["max_evidence_age_days"] == 21


def test_generic_retrieval_time_is_not_promoted_to_official_check_time(tmp_path):
    evidence_dir = tmp_path / "04-journals" / "journal-evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "target-journal.json").write_text(
        json.dumps({"retrieved_at": "2026-09-28T00:00:00Z", "max_evidence_age_days": 21}),
        encoding="utf-8",
    )

    resolved = resolve_inputs(str(tmp_path))

    assert resolved["evidence_checked_at"] is None
