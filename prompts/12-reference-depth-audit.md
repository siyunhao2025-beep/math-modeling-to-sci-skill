# S8.1 — Reference Reality & Citation-Depth Audit

## Objective

Eliminate fabricated, malformed, stale or contextually wrong citations before submission.

## Phase A — bibliographic identity

1. Run `scripts/readiness/reference_verifier.py` on the working `.bib`.
2. Crossref is the primary DOI metadata source. Use Semantic Scholar and PubMed as independent corroborating sources when available.
3. Normalize DOI, title, author list, journal, year, volume/issue/pages and canonical URL.
4. If providers disagree materially, mark `CONFLICT`; do not silently pick the convenient record.
5. In strict mode, only API-verified references enter `references.clean.bib`.
6. A reference without a DOI may be retained only after authoritative source verification by the Agent and explicit author approval; record why DOI verification is unavailable.

## Phase B — contextual citation support

For every material citation occurrence, create a record:

- citation id / manuscript location;
- exact manuscript claim being supported;
- cited reference key + DOI/PMID if known;
- evidence available from the cited paper: title, abstract, methods/results excerpt if legally/technically available;
- status: `SUPPORTS`, `PARTIALLY_SUPPORTS`, `BACKGROUND_ONLY`, `CONTRADICTS`, `DOES_NOT_SUPPORT`, `CANNOT_VERIFY`;
- confidence: high / medium / low;
- action: keep / narrow claim / replace citation / add citation / author check.

Do **not** infer support merely because title keywords overlap.

### High-risk mis-citation cases

Treat as blocker when:

- a review is cited as though it were the primary experiment and the claim requires primary evidence;
- a paper reports association but the manuscript cites it for causality;
- a model/simulation paper is cited as direct observation;
- a cited study population, regime, altitude/latitude, material, species, dataset or experimental condition differs materially from the manuscript claim;
- the cited paper actually reports the opposite trend;
- a secondary source is the only support for a precise quantitative number that should be sourced to the primary work.

## Output

Write `08-readiness/citation-support-audit.json` with:

```json
{
  "citations": [
    {
      "id": "cite-audit-1",
      "location": "sec-2/block-4",
      "claim": "...",
      "reference_key": "...",
      "doi": "...",
      "status": "SUPPORTS",
      "confidence": "high",
      "reason": "...",
      "action": "keep"
    }
  ],
  "blockers": [],
  "warnings": []
}
```

`CONTRADICTS` and `DOES_NOT_SUPPORT` are hard blockers. `CANNOT_VERIFY` requires author review unless the claim is removed.
