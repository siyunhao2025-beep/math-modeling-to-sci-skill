# S8.2 — Deep Journal Fit & Desk-Reject Risk

## Objective

Replace shallow seed-tag matching with current, evidence-backed journal fit analysis.

## Required current evidence

Before rating fit, verify and save:

1. official journal Aims & Scope text + source URL + retrieval date;
2. current article types and their definitions/limits + source URL;
3. current submission instructions that matter for desk review (word/figure/table/reference limits, abstract type, data/ethics requirements, special formats);
4. recent 12-month content: use recent published/online papers from Crossref and, when available, journal-published “articles in press/accepted” pages verified by the Agent. Never call Crossref records “accepted articles” unless the source explicitly says so.

Run `scripts/readiness/journal_fit.py` to create a reproducible lexical baseline. Then perform an Agent semantic review.

## Semantic fit questions

Score each 0–5 with evidence:

- scientific problem fit;
- method/data fit;
- audience fit;
- novelty/contribution fit;
- article-type fit;
- evidence-strength fit;
- format/practical fit.

For each dimension cite the official scope or recent-paper evidence used. Do not use IF/quartile as a substitute for scope fit.

## Desk-reject risk list

Explicitly assess:

- scope mismatch;
- wrong article type;
- contribution too incremental for this journal;
- method/data class rarely published by the journal;
- recent journal content shows a different audience than the manuscript;
- abstract/word/figure/table/reference limits exceeded;
- mandatory reporting/ethics/data/code elements missing;
- template/submission-file mismatch;
- stale/uncertain indexing/APC/metric claims.

Use `HIGH / MEDIUM / LOW`, with a concrete reason and mitigation. Do not invent acceptance probability.

## Decision

Output one of:

- `STRONG_FIT` — no material scope/article-type blocker;
- `PLAUSIBLE_FIT` — some manageable risk;
- `WEAK_FIT` — likely editorial mismatch;
- `BLOCKED_NEEDS_CURRENT_EVIDENCE` — official evidence incomplete.

Write semantic results back into `08-readiness/journal-fit.json` under `agent_semantic_review` without deleting the deterministic baseline fields.
