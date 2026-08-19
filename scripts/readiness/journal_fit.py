#!/usr/bin/env python3
"""Deep journal-fit baseline using official scope text + recent Crossref records.

This script deliberately does not scrape publisher pages heuristically. The Agent
must first verify the current official Aims & Scope/article-type pages and save
those texts/constraints as inputs. Crossref supplies recent published/online
journal articles as an auditable recent-content baseline.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import os
from pathlib import Path
import statistics
import sys
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import cosine_similarity, ir_text, load_json, save_json  # noqa: E402

CROSSREF = "https://api.crossref.org"


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
        months: int = 12, limit: int = 100, mailto: str | None = None,
        recent_cache: str | None = None) -> dict:
    text = manuscript_text(manuscript)
    scope = Path(aims_scope_file).read_text(encoding="utf-8") if Path(aims_scope_file).is_file() else ""
    if recent_cache and Path(recent_cache).is_file():
        recent = load_json(recent_cache)
        if isinstance(recent, dict):
            recent = recent.get("articles", [])
    else:
        try:
            recent = recent_crossref(issn, months, limit, mailto)
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
    if not scope.strip() or not scope_source_url:
        blockers.append("official Aims & Scope text/provenance missing")
    if not article_type_verified:
        blockers.append("article type not verified against current journal guidance")
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
        "issn": issn,
        "article_type": article_type,
        "article_type_verified": article_type_verified,
        "allowed_article_types": allowed_types,
        "official_evidence": {
            "aims_scope_source_url": scope_source_url,
            "article_type_source_url": article_type_source_url,
            "aims_scope_file": aims_scope_file,
        },
        "recent_corpus": {
            "source": "Crossref recent published/online journal records unless a verified cache was supplied",
            "months": months,
            "count": len(recent),
            "mean_similarity": recent_mean,
            "top10_mean_similarity": recent_top10,
            "items": sorted([dict(x, similarity=s) for x, s in zip(recent, recent_scores)], key=lambda x: x["similarity"], reverse=True)[:20],
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
    ap.add_argument("--recent-cache")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--mailto", default=os.getenv("CROSSREF_MAILTO"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = run(args.manuscript, args.journal_name, args.issn, args.aims_scope_file, args.out,
                 article_types_file=args.article_types_file, article_type=args.article_type,
                 scope_source_url=args.scope_source_url, article_type_source_url=args.article_type_source_url,
                 months=args.months, limit=args.limit, mailto=args.mailto, recent_cache=args.recent_cache)
    print(f"fit={result['baseline_fit_score_0_100']} blockers={len(result['blockers'])} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
