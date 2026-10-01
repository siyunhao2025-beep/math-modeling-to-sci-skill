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

## Optional target-journal writing-pattern profile

Journal fit and journal writing style are different questions. Only after the target journal and article type are
resolved may an author choose to learn structural or rhetorical patterns from lawfully accessed full texts. This
profile is optional and its absence is not a journal-fit blocker.

1. Use papers from the same journal and article type. Lock each source by DOI/URL and file SHA-256.
2. Split train and held-out papers by author group before extracting observations; the same team or another version
   of the same paper must not cross the split.
3. Record paraphrased observations with page/section/paragraph locators. Do not store quotations, excerpts, full
   text, scientific findings, numerical results, or paper-specific claims in the profile.
4. Set project-specific minimums explicitly and run `scripts/readiness/journal_style_profile.py`. A first pass remains
   `DRAFT_NEEDS_HELDOUT_EVALUATION`; do not silently treat it as usable.
5. Evaluate the compiled profile on the held-out author group and record human checks for scientific-content,
   number/unit/formula, citation, structure, and non-mimicry preservation. Load the resulting profile—not the source
   corpus—during manuscript revision.

The profile may guide article structure, model-description order, validation reporting, result interpretation, and
limitations rhetoric. It cannot modify facts, equations, numbers, units, citation keys, evidence strength, model
results, or the claim ceiling. An unobserved pattern is not evidence that the journal rejects it; an observed pattern
is not an official requirement. Current official instructions always control compliance.

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
