#!/usr/bin/env python3
"""Deep journal-fit baseline using official scope text + recent Crossref records.

This script deliberately does not scrape publisher pages heuristically. The Agent
must first verify the current official Aims & Scope/article-type pages and save
those texts/constraints as inputs. Crossref supplies recent published/online
journal articles as an auditable recent-content baseline.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import re
import statistics
import sys
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import cosine_similarity, ir_text, load_json, save_json  # noqa: E402

CROSSREF = "https://api.crossref.org"


def normalize_issn(value: str) -> str | None:
    """Return a canonical ISSN only when its syntax and check digit are valid."""
    compact = (value or "").strip().replace("-", "").replace(" ", "").upper()
    if not re.fullmatch(r"[0-9]{7}[0-9X]", compact):
        return None
    total = sum(int(char) * weight for char, weight in zip(compact[:7], range(8, 1, -1)))
    check = (11 - total % 11) % 11
    expected = "X" if check == 10 else str(check)
    if compact[-1] != expected:
        return None
    return compact[:4] + "-" + compact[4:]


def evidence_freshness(checked_at: str | None, max_age_days: int | None,
                       *, now: datetime | None = None) -> dict:
    """Classify official journal evidence against an explicit operational age policy."""
    if not checked_at:
        return {"status": "UNVERIFIED", "checked_at": None, "age_days": None,
                "max_age_days": max_age_days}
    if max_age_days is None:
        return {"status": "POLICY_UNSET", "checked_at": checked_at, "age_days": None,
                "max_age_days": None}
    if max_age_days < 0:
        raise ValueError("max_evidence_age_days must be non-negative")
    try:
        parsed = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    except ValueError:
        return {"status": "INVALID_TIMESTAMP", "checked_at": checked_at, "age_days": None,
                "max_age_days": max_age_days}
    if parsed.tzinfo is None:
        return {"status": "INVALID_TIMESTAMP", "checked_at": checked_at, "age_days": None,
                "max_age_days": max_age_days}
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    age_seconds = (current.astimezone(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    if age_seconds < 0:
        return {"status": "FUTURE_TIMESTAMP", "checked_at": checked_at,
                "age_days": round(age_seconds / 86400, 3), "max_age_days": max_age_days}
    age_days = age_seconds / 86400
    return {"status": "CURRENT" if age_days <= max_age_days else "STALE",
            "checked_at": checked_at, "age_days": round(age_days, 3),
            "max_age_days": max_age_days}


def manuscript_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".json":
        try:
            return ir_text(load_json(path))
        except Exception:
            pass
    return p.read_text(encoding="utf-8")


def recent_crossref(issn: str, months: int = 12, limit: int = 100, mailto: str | None = None) -> list[dict]:
    since = date.today() - timedelta(days=round(months * 30.4375))
    params = {
        "filter": f"from-pub-date:{since.isoformat()},type:journal-article",
        "rows": min(max(limit, 1), 1000),
        "sort": "published",
        "order": "desc",
    }
    if mailto:
        params["mailto"] = mailto
    r = requests.get(f"{CROSSREF}/journals/{quote(issn, safe='')}/works", params=params, timeout=20)
    r.raise_for_status()
    items = (r.json().get("message") or {}).get("items") or []
    out = []
    for item in items:
        title = (item.get("title") or [""])[0]
        abstract = item.get("abstract") or ""
        out.append({
            "doi": item.get("DOI"),
            "title": title,
            "abstract": abstract,
            "type": item.get("type"),
            "publisher": item.get("publisher"),
        })
    return out


def run(manuscript: str, journal_name: str, issn: str, aims_scope_file: str, out: str,
        *, article_types_file: str | None = None, article_type: str | None = None,
        scope_source_url: str | None = None, article_type_source_url: str | None = None,
        evidence_checked_at: str | None = None, max_evidence_age_days: int | None = None,
        months: int = 12, limit: int = 100, mailto: str | None = None,
        recent_cache: str | None = None, now: datetime | None = None) -> dict:
    text = manuscript_text(manuscript)
    scope = Path(aims_scope_file).read_text(encoding="utf-8") if Path(aims_scope_file).is_file() else ""
    canonical_issn = normalize_issn(issn)
    freshness = evidence_freshness(evidence_checked_at, max_evidence_age_days, now=now)
    if recent_cache and Path(recent_cache).is_file():
        recent = load_json(recent_cache)
        if isinstance(recent, dict):
            recent = recent.get("articles", [])
        fetch_error = None
    elif not canonical_issn:
        recent = []
        fetch_error = "recent corpus not fetched because the ISSN identity is invalid"
    else:
        try:
            recent = recent_crossref(canonical_issn or issn, months, limit, mailto)
        except Exception as exc:
            recent = []
            fetch_error = str(exc)
        else:
            fetch_error = None

    recent_scores = [cosine_similarity(text, (x.get("title") or "") + " " + (x.get("abstract") or "")) for x in recent]
    scope_score = cosine_similarity(text, scope)
    recent_mean = round(statistics.fmean(recent_scores), 4) if recent_scores else 0.0
    recent_top10 = round(statistics.fmean(sorted(recent_scores, reverse=True)[:10]), 4) if recent_scores else 0.0

    allowed_types: list[str] = []
    if article_types_file and Path(article_types_file).is_file():
        allowed_types = [x.strip() for x in Path(article_types_file).read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
    article_type_verified = bool(article_type and allowed_types and any(article_type.lower() == x.lower() for x in allowed_types))

    risks = []
    blockers = []
    if not canonical_issn:
        blockers.append("journal identity is not anchored to a valid ISSN")
    if not scope.strip() or not scope_source_url:
        blockers.append("official Aims & Scope text/provenance missing")
    if not article_type_verified or not article_type_source_url:
        blockers.append("article type not verified against current journal guidance")
    if freshness["status"] != "CURRENT":
        blockers.append(f"official journal requirements are not current ({freshness['status'].lower()})")
    if scope_score < 0.12:
        risks.append({"code": "SCOPE_LOW", "severity": "high", "detail": f"lexical scope similarity is low ({scope_score})"})
    if recent and recent_top10 < 0.10:
        risks.append({"code": "RECENT_CORPUS_LOW", "severity": "high", "detail": f"similarity to the most related recent papers is low ({recent_top10})"})
    if not recent:
        risks.append({"code": "RECENT_CORPUS_UNAVAILABLE", "severity": "medium", "detail": fetch_error or "no recent Crossref records returned"})

    # Reproducible baseline only. Agent semantic judgment is recorded separately.
    score = round(100 * (0.50 * min(scope_score / 0.30, 1.0) + 0.35 * min(recent_top10 / 0.25, 1.0) + 0.15 * (1.0 if article_type_verified else 0.0)), 1)
    result = {
        "schema_version": "1.0",
        "journal": journal_name,
        "issn": canonical_issn or issn,
        "journal_identity": {
            "key": f"issn:{canonical_issn}" if canonical_issn else None,
            "status": "RESOLVED" if canonical_issn else "UNRESOLVED",
        },
        "article_type": article_type,
        "article_type_verified": article_type_verified,
        "allowed_article_types": allowed_types,
        "official_evidence": {
            "source_class": "official_requirement",
            "aims_scope_source_url": scope_source_url,
            "article_type_source_url": article_type_source_url,
            "aims_scope_file": aims_scope_file,
            "freshness": freshness,
        },
        "recent_corpus": {
            "source_class": "observed_pattern",
            "source": "Crossref recent published/online journal records unless a verified cache was supplied",
            "months": months,
            "count": len(recent),
            "mean_similarity": recent_mean,
            "top10_mean_similarity": recent_top10,
            "items": sorted([dict(x, similarity=s) for x, s in zip(recent, recent_scores)], key=lambda x: x["similarity"], reverse=True)[:20],
            "important_limit": "Observed article patterns cannot establish current author requirements or policies.",
        },
        "scope_similarity": scope_score,
        "baseline_fit_score_0_100": score,
        "risks": risks,
        "blockers": blockers,
        "ready_for_agent_semantic_review": not blockers,
        "important_limit": "This deterministic score is a lexical/reproducible baseline, not a substitute for semantic scope review by the Agent/editorial judgment.",
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--journal-name", required=True)
    ap.add_argument("--issn", required=True)
    ap.add_argument("--aims-scope-file", required=True)
    ap.add_argument("--scope-source-url", required=True)
    ap.add_argument("--article-types-file")
    ap.add_argument("--article-type")
    ap.add_argument("--article-type-source-url")
    ap.add_argument("--evidence-checked-at",
                    help="Timezone-aware ISO-8601 time when official journal pages were checked")
    ap.add_argument("--max-evidence-age-days", type=int,
                    help="Project-defined operational freshness limit; not a scientific threshold")
    ap.add_argument("--recent-cache")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--mailto", default=os.getenv("CROSSREF_MAILTO"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = run(args.manuscript, args.journal_name, args.issn, args.aims_scope_file, args.out,
                 article_types_file=args.article_types_file, article_type=args.article_type,
                 scope_source_url=args.scope_source_url, article_type_source_url=args.article_type_source_url,
                 evidence_checked_at=args.evidence_checked_at,
                 max_evidence_age_days=args.max_evidence_age_days,
                 months=args.months, limit=args.limit, mailto=args.mailto, recent_cache=args.recent_cache)
    print(f"fit={result['baseline_fit_score_0_100']} blockers={len(result['blockers'])} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
