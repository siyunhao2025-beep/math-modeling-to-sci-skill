# Integrated SCI Extension Router

This router prevents post-v1.0 extension prompts from becoming orphan files or being mistaken for deterministic Python stages.

## Route by task

| Task | Load | Runtime relationship |
|---|---|---|
| Math-modeling report → SCI paper | `00-orchestrator.md` | canonical S1–S7 pipeline |
| General SCI paper planning/drafting | `08-sci-writing.md` | Agent module W |
| Academic English polishing/revision | `09-language-polish.md` | Agent module P |
| Journal matching/submission preparation | `10-submission-journal-search.md` | Agent module J |
| Reference verification / citation depth | `11-publication-readiness-orchestrator.md` → `12-reference-depth-audit.md` | post-S6 S8 suite |
| Deep journal fit / desk-reject risk | `11-publication-readiness-orchestrator.md` → `13-journal-fit-deep.md` | post-S6 S8 suite |
| Claim–Evidence Audit | `11-publication-readiness-orchestrator.md` → `14-claim-evidence-audit.md` | post-S6 S8 suite |
| Figure/table scientific review | `11-publication-readiness-orchestrator.md` → `15-figure-table-audit.md` | post-S6 S8 suite |
| Reviewer Simulator / rebuttal loop | `11-publication-readiness-orchestrator.md` → `16-reviewer-simulator.md` | post-S6 S8 suite |
| One-click submission audit | `11-publication-readiness-orchestrator.md` → `17-submission-preflight.md` | deterministic aggregator + Agent evidence |
| Reporting/methods/ethics compliance | `11-publication-readiness-orchestrator.md` → `18-methods-reporting-ethics.md` | post-S6 S8 suite |

For W/P/J/S8 always also load:

- `shared/role-preamble.md`
- `shared/05-integrity-preservation.md`

Load `shared/io-contract.md` when the task produces/consumes structured manuscript artifacts.

## Mixed tasks

When the user asks for several operations, use the minimum necessary chain:

- draft + polish → W → P
- polish + journal selection → P → J
- full general manuscript preparation → W → P → J
- publication-readiness audit → S8 orchestrator
- math-modeling conversion + full submission preparation → S1–S6 → S8 → final report/package

`S8` is a logical post-S6 Agent/readiness layer. It does **not** renumber the legacy Python `S1–S7` configuration. The deterministic S8 utilities live under `scripts/readiness/`; semantic checks remain explicit Agent tasks.

## Preservation rule for non-IR tasks

W/P/J/S8 may be invoked on ordinary prose or a manuscript that never passed through S1. In that case **do not claim that IR-based G2/G6 checks ran**. Instead build a protected-span/source ledger from the supplied manuscript and explicitly preserve formulas, values, units, citations, figure/table references, and claim strength as defined in `shared/05-integrity-preservation.md`.

## Current-information rule

Journal policies, impact metrics, APCs, templates, indexing, article types, reporting-guideline versions and submission requirements are time-sensitive. Module J/S8 must verify them from current authoritative sources at execution time and record retrieval dates. A local seed value is never sufficient for a final submission decision.

Reference identity verification should use `scripts/readiness/reference_verifier.py`; journal-fit evidence should use current official scope/article-type pages plus `scripts/readiness/journal_fit.py` as a reproducible baseline. API metadata verifies identity/provenance, not whether a citation semantically supports a claim.

## Output truthfulness

- Do not label a manuscript `SUBMISSION_READY` merely because language polishing completed.
- The strongest automated readiness label is `READY_FOR_HUMAN_SUBMISSION_CHECK`.
- Do not claim S8 semantic modules were executed by `scripts/run_pipeline.py`; they were not.
- Do not describe simulated reviewers as real reviewers or output fake acceptance probabilities.
- Do not describe Semantic Scholar similarity precheck as iThenticate/Turnitin/plagiarism percentage.
- If a module relies on inference rather than direct evidence, label that inference and preserve the original scientific claim strength.
