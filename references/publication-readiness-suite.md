# Publication Readiness Suite — Feature Map

This suite addresses preventable submission failures that remain after ordinary manuscript writing and S1–S6 validation.

## P0 — editorial/reviewer critical

- **Reference Reality Layer**: Crossref primary DOI verification, Semantic Scholar/PubMed corroboration, strict clean BibTeX, unverified/conflicting references blocked.
- **Citation Depth Audit**: verifies whether a cited paper supports the exact manuscript claim; metadata identity alone is insufficient.
- **Deep Journal Fit**: current official Aims & Scope, current article type, recent 12-month journal-content baseline, semantic fit review, desk-reject risk list.
- **Reviewer Simulator**: handling editor + domain + methods/statistics + skeptical reviewer; 3–5 substantive comments, up to 3 revision/rebuttal rounds.
- **Claim–Evidence Audit**: key claims mapped to source data/figures/tables/equations/statistics/verified citations; unsupported high-risk claims block release.

## P1 — major quality/compliance gains

- reporting guideline detection and current-official-checklist verification (PRISMA/STROBE/TRIPOD/ARRIVE/CONSORT/STARD when applicable);
- methods/statistics checks for sample-size rationale, uncertainty/error bars, p-values, effect sizes, multiple testing, missing data, randomization/blinding and reproducibility;
- optional LanguageTool diagnostics plus internal academic-register/overclaim checks;
- ethics, consent, data availability, code availability, COI and funding checks; approval IDs are never fabricated.

## P2 — submission hygiene

- advisory similar-paper/text-overlap precheck using scholarly discovery APIs; explicitly not iThenticate/Turnitin;
- data/code/supplement reproducibility manifest guidance;
- verified official-template provenance and hard LaTeX compilation gate for LaTeX submissions.

## Final gate

`submission_preflight.py` aggregates S6 + S8 and emits only:

- `BLOCKED`
- `AUTHOR_ACTION_REQUIRED`
- `READY_FOR_HUMAN_SUBMISSION_CHECK`

No feature claims to predict or guarantee acceptance.
