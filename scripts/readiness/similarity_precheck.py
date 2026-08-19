#!/usr/bin/env python3
"""Advisory scholarly-text similarity precheck.

This queries Semantic Scholar for papers related to the manuscript title and
compares title/abstract token overlap. It is NOT iThenticate, Turnitin, or a
publisher plagiarism database and must never be described as one.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import cosine_similarity, load_json, save_json, title_similarity  # noqa: E402

S2 = "https://api.semanticscholar.org/graph/v1"


def manuscript_meta(path: str) -> tuple[str, str]:
    p = Path(path)
    if p.suffix.lower() == ".json":
        d = load_json(path)
        meta = d.get("meta", {})
        return meta.get("title") or "", meta.get("abstract") or ""
    text = p.read_text(encoding="utf-8")
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    return (lines[0] if lines else ""), text[:5000]


def run(manuscript: str, out: str, api_key: str | None = None, limit: int = 20) -> dict:
    title, abstract = manuscript_meta(manuscript)
    headers = {"x-api-key": api_key} if api_key else {}
    params = {"query": title, "limit": min(max(limit, 1), 100), "fields": "title,abstract,year,venue,externalIds,url"}
    try:
        r = requests.get(f"{S2}/paper/search", params=params, headers=headers, timeout=20)
        r.raise_for_status()
        papers = r.json().get("data", [])
        error = None
    except Exception as exc:
        papers, error = [], str(exc)
    matches = []
    for p in papers:
        ts = title_similarity(title, p.get("title") or "")
        a = abstract or ""
        b = p.get("abstract") or ""
        ass = cosine_similarity(a, b) if a and b else 0.0
        matches.append({
            "paper_id": p.get("paperId"),
            "title": p.get("title"),
            "year": p.get("year"),
            "venue": p.get("venue"),
            "doi": (p.get("externalIds") or {}).get("DOI"),
            "url": p.get("url"),
            "title_similarity": ts,
            "abstract_similarity": ass,
            "flag": "HIGH" if ts >= 0.92 or ass >= 0.82 else ("REVIEW" if ts >= 0.75 or ass >= 0.65 else "LOW"),
        })
    matches.sort(key=lambda x: max(x["title_similarity"], x["abstract_similarity"]), reverse=True)
    result = {
        "schema_version": "1.0",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if error is None else "unavailable",
        "error": error,
        "matches": matches,
        "high_flags": [m for m in matches if m["flag"] == "HIGH"],
        "important_limit": "Advisory discovery only. This is not a plagiarism score and is not equivalent to iThenticate/Turnitin/publisher similarity screening.",
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--s2-api-key", default=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    result = run(args.manuscript, args.out, args.s2_api_key, args.limit)
    print(f"status={result['status']} high_flags={len(result['high_flags'])} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
