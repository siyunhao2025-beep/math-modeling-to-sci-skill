#!/usr/bin/env python3
"""Reference verification against Crossref, Semantic Scholar and PubMed.

The verifier is deliberately conservative. Crossref is treated as the primary
DOI metadata source. Semantic Scholar and PubMed provide independent corroboration
when available. A reference that cannot be verified is never silently promoted to
"verified" and, in strict mode, is omitted from the clean BibTeX output.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402
from readiness.utils import save_json, title_similarity  # noqa: E402

CROSSREF = "https://api.crossref.org"
S2 = "https://api.semanticscholar.org/graph/v1"
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DOI_RE = re.compile(r"10\.\d{4,9}/\S+", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().strip("{}<>").replace("https://doi.org/", "").replace("http://doi.org/", "")
    m = DOI_RE.search(v)
    return m.group(0).rstrip(".,;)") if m else None


def _request_json(url: str, *, params=None, headers=None, timeout=15, retries=2):
    last = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
            if r.status_code == 404:
                return None, 404
            if r.status_code == 429 and attempt < retries:
                time.sleep(1.0 + attempt)
                continue
            r.raise_for_status()
            return r.json(), r.status_code
        except Exception as exc:  # network failures are evidence gaps, not PASS
            last = exc
            if attempt < retries:
                time.sleep(0.5 + attempt)
    return {"error": str(last)}, None


def crossref_lookup(doi: str, mailto: str | None = None) -> dict:
    params = {"mailto": mailto} if mailto else None
    data, status = _request_json(f"{CROSSREF}/works/{quote(doi, safe='')}", params=params)
    if not data or status != 200:
        return {"provider": "crossref", "found": False, "status": status, "raw_error": data}
    item = data.get("message", {})
    title = (item.get("title") or [None])[0]
    container = (item.get("container-title") or [None])[0]
    year = None
    for key in ("published-print", "published-online", "published", "issued", "created"):
        parts = ((item.get(key) or {}).get("date-parts") or [])
        if parts and parts[0]:
            year = parts[0][0]
            break
    return {
        "provider": "crossref",
        "found": True,
        "doi": normalize_doi(item.get("DOI")) or doi,
        "title": title,
        "authors": [" ".join(x for x in [a.get("given"), a.get("family")] if x) for a in item.get("author", [])],
        "year": year,
        "journal": container,
        "volume": item.get("volume"),
        "issue": item.get("issue"),
        "pages": item.get("page"),
        "publisher": item.get("publisher"),
        "type": item.get("type"),
        "url": item.get("URL"),
        "abstract": item.get("abstract"),
        "retrieved_at": now(),
    }


def semantic_scholar_lookup(doi: str, api_key: str | None = None) -> dict:
    headers = {"x-api-key": api_key} if api_key else {}
    pid = quote("DOI:" + doi, safe=":")
    fields = "paperId,title,authors,year,venue,externalIds,citationCount,referenceCount,abstract,url"
    data, status = _request_json(f"{S2}/paper/{pid}", params={"fields": fields}, headers=headers)
    if not data or status != 200:
        return {"provider": "semantic_scholar", "found": False, "status": status, "raw_error": data}
    external = data.get("externalIds") or {}
    return {
        "provider": "semantic_scholar",
        "found": True,
        "paper_id": data.get("paperId"),
        "doi": normalize_doi(external.get("DOI")) or doi,
        "pmid": external.get("PubMed"),
        "title": data.get("title"),
        "authors": [a.get("name") for a in data.get("authors", []) if a.get("name")],
        "year": data.get("year"),
        "journal": data.get("venue"),
        "citation_count": data.get("citationCount"),
        "reference_count": data.get("referenceCount"),
        "abstract": data.get("abstract"),
        "url": data.get("url"),
        "retrieved_at": now(),
    }


def pubmed_lookup(doi: str, api_key: str | None = None, email: str | None = None) -> dict:
    params = {"db": "pubmed", "term": f"{doi}[aid]", "retmode": "json", "retmax": 5}
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email
    search, status = _request_json(f"{NCBI}/esearch.fcgi", params=params)
    ids = (((search or {}).get("esearchresult") or {}).get("idlist") or []) if status == 200 else []
    if not ids:
        return {"provider": "pubmed", "found": False, "status": status, "raw_error": search}
    sp = {"db": "pubmed", "id": ids[0], "retmode": "json"}
    if api_key:
        sp["api_key"] = api_key
    if email:
        sp["email"] = email
    summary, s2 = _request_json(f"{NCBI}/esummary.fcgi", params=sp)
    if not summary or s2 != 200:
        return {"provider": "pubmed", "found": True, "pmid": ids[0], "summary_available": False}
    rec = (summary.get("result") or {}).get(ids[0], {})
    return {
        "provider": "pubmed",
        "found": True,
        "pmid": ids[0],
        "doi": doi,
        "title": rec.get("title"),
        "authors": [a.get("name") for a in rec.get("authors", []) if a.get("name")],
        "year": int(rec.get("pubdate", "0")[:4]) if str(rec.get("pubdate", ""))[:4].isdigit() else None,
        "journal": rec.get("fulljournalname") or rec.get("source"),
        "retrieved_at": now(),
    }


def _load_bib(path: str) -> list[dict]:
    import bibtexparser
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return list(db.entries)


def _bib_entry_from_crossref(key: str, cr: dict) -> str:
    fields = []
    def add(name, value):
        if value not in (None, "", []):
            if isinstance(value, list):
                value = " and ".join(value)
            fields.append(f"  {name} = {{{str(value)}}}")
    add("title", html.unescape(cr.get("title") or ""))
    add("author", cr.get("authors"))
    add("journal", cr.get("journal"))
    add("year", cr.get("year"))
    add("volume", cr.get("volume"))
    add("number", cr.get("issue"))
    add("pages", cr.get("pages"))
    add("doi", cr.get("doi"))
    add("url", cr.get("url"))
    entry_type = "article" if cr.get("type") in ("journal-article", None) else "misc"
    return f"@{entry_type}{{{key},\n" + ",\n".join(fields) + "\n}"


def verify_entry(entry: dict, *, mailto=None, s2_key=None, ncbi_key=None) -> dict:
    key = entry.get("ID") or entry.get("id") or "unknown"
    doi = normalize_doi(entry.get("doi") or entry.get("url"))
    if not doi:
        return {
            "key": key,
            "status": "unverified",
            "reason": "no DOI present",
            "original": {"title": entry.get("title"), "year": entry.get("year")},
            "providers": [],
        }
    cr = crossref_lookup(doi, mailto)
    ss = semantic_scholar_lookup(doi, s2_key)
    pm = pubmed_lookup(doi, ncbi_key, mailto)
    providers = [cr, ss, pm]
    found = [p for p in providers if p.get("found")]
    title0 = entry.get("title") or ""
    title_scores = {p["provider"]: title_similarity(title0, p.get("title") or "") for p in found if p.get("title")}
    doi_agree = [p for p in found if normalize_doi(p.get("doi")) == doi]
    conflicts = []
    if cr.get("found") and title0 and title_similarity(title0, cr.get("title") or "") < 0.55:
        conflicts.append("Crossref title strongly disagrees with BibTeX title")
    years = {str(p.get("year")) for p in found if p.get("year")}
    if len(years) > 1:
        conflicts.append(f"provider year disagreement: {sorted(years)}")
    if conflicts:
        status = "conflict"
    elif cr.get("found") and len(doi_agree) >= 2:
        status = "verified_consensus"
    elif cr.get("found"):
        status = "verified_primary"
    else:
        status = "unverified"
    return {
        "key": key,
        "doi": doi,
        "status": status,
        "title_similarity": title_scores,
        "conflicts": conflicts,
        "original": {"title": entry.get("title"), "year": entry.get("year"), "journal": entry.get("journal")},
        "providers": providers,
        "canonical": cr if cr.get("found") else (found[0] if found else None),
    }


def run(bib: str, out: str, clean_bib: str | None = None, *, mailto=None, s2_key=None, ncbi_key=None) -> dict:
    entries = _load_bib(bib)
    results = [verify_entry(e, mailto=mailto, s2_key=s2_key, ncbi_key=ncbi_key) for e in entries]
    verified = [r for r in results if r["status"].startswith("verified_")]
    blockers = [r for r in results if r["status"] in ("unverified", "conflict")]
    payload = {
        "schema_version": "1.0",
        "verified_at": now(),
        "input_bib": os.path.abspath(bib),
        "providers": ["crossref", "semantic_scholar", "pubmed"],
        "summary": {
            "total": len(results),
            "verified": len(verified),
            "blocked": len(blockers),
            "clean_bib_policy": "strict: only API-verified references are retained",
        },
        "references": results,
        "blockers": [{"key": r["key"], "status": r["status"], "reason": r.get("reason") or "; ".join(r.get("conflicts") or [])} for r in blockers],
        "ready": not blockers,
    }
    save_json(out, payload)
    if clean_bib:
        by_key = {e.get("ID"): e for e in entries}
        lines = []
        for r in verified:
            canonical = r.get("canonical") or {}
            if canonical.get("provider") == "crossref":
                lines.append(_bib_entry_from_crossref(r["key"], canonical))
            else:
                # A verified DOI without Crossref canonical metadata is not emitted in strict mode.
                continue
        Path(clean_bib).parent.mkdir(parents=True, exist_ok=True)
        Path(clean_bib).write_text("\n\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--clean-bib")
    ap.add_argument("--mailto", default=os.getenv("CROSSREF_MAILTO"))
    ap.add_argument("--s2-api-key", default=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
    ap.add_argument("--ncbi-api-key", default=os.getenv("NCBI_API_KEY"))
    args = ap.parse_args()
    result = run(args.bib, args.out, args.clean_bib, mailto=args.mailto, s2_key=args.s2_api_key, ncbi_key=args.ncbi_api_key)
    print(f"verified={result['summary']['verified']} blocked={result['summary']['blocked']} -> {args.out}")
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
