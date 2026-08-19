# Integrated SCI Extension Router

This router prevents the three post-v1.0 extension prompts from becoming orphan files or being mistaken for additional CLI stages.

## Route by task

| Task | Load | Runtime relationship |
|---|---|---|
| Math-modeling report → SCI paper | `00-orchestrator.md` | canonical S1–S7 pipeline |
| General SCI paper planning/drafting | `08-sci-writing.md` | Agent module W; not a Python stage |
| Academic English polishing/revision | `09-language-polish.md` | Agent module P; not a Python stage |
| Journal matching/submission preparation/reviewer response | `10-submission-journal-search.md` | Agent module J; not a Python stage |

For W/P/J always also load:

- `shared/role-preamble.md`
- `shared/05-integrity-preservation.md`

Load `shared/io-contract.md` when the task produces/consumes structured manuscript artifacts.

## Mixed tasks

When the user asks for several operations, use the minimum necessary chain:

- draft + polish → W → P
- polish + journal selection → P → J
- full general manuscript preparation → W → P → J
- math-modeling conversion + extra polishing/submission work → S1–S7 first, then P/J only if still requested

## Preservation rule for non-IR tasks

W/P/J may be invoked on ordinary prose or a manuscript that never passed through S1. In that case **do not claim that IR-based G2/G6 checks ran**. Instead build a protected-span/source ledger from the supplied manuscript and explicitly preserve formulas, values, units, citations, figure/table references, and claim strength as defined in `shared/05-integrity-preservation.md`.

## Current-information rule

Journal policies, impact metrics, APCs, templates, indexing, and submission requirements are time-sensitive. Module J must verify them from current authoritative sources at execution time and record retrieval dates. A local seed value is never sufficient for a final submission decision.

## Output truthfulness

- Do not label a manuscript `SUBMISSION_READY` merely because language polishing completed.
- Do not claim an extension module was executed by `scripts/run_pipeline.py`; it was not.
- If a module relies on inference rather than direct evidence, label that inference and preserve the original scientific claim strength.
