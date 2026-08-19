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

## User-guidance route

Load `shared/06-user-guidance-playbook.md` when any of these applies:

- the user uploads Word/LaTeX/LaTeX-project content but does not know what to ask;
- the user asks “怎么提问 / 下一步怎么做 / 怎么使用这个 Skill”; 
- the user replies only “继续 / 下一步 / 按你建议来”; 
- a stage has just completed and a concrete next-step prompt would help;
- the user asks for a full workflow without knowing the S1–S8 terminology.

For an ambiguous fresh upload, default to a **read-only intake/diagnostic pass** before changing manuscript content. After each completed stage, give one recommended next action and one directly copyable prompt. If the user says only “继续/下一步”, infer the next valid stage from completed artifacts rather than forcing them to restate a technical command.

If the user explicitly chooses “完整流程 / 全自动”, continue through the valid chain until a genuine author decision, missing-evidence blocker, target-journal decision, or verification requirement needs input. Do not repeatedly ask them to copy the example prompts.

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
