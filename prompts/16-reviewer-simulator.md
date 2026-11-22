# S8.5 — Reviewer Simulator & Revision/Rebuttal Loop

## Role

Simulate the most consequential editorial/reviewer objections **before** submission. This is adversarial pre-review, not praise generation.

## Required evidence

Read:

- target journal + current Aims & Scope/article type;
- manuscript/IR/build;
- S6 validation;
- reference verification + citation-support audit;
- journal-fit audit;
- claim–evidence audit;
- figure/table audit;
- methods/reporting/ethics compliance audit.

Before scoring or drafting comments, record a machine-readable `review_coverage` ledger. It must account exactly once for these input IDs:

- `manuscript`
- `journal_scope`
- `validation_results`
- `citation_identity_support`
- `claim_evidence`
- `figure_table`
- `methods_reporting_compliance`

For each input use `REVIEWED`, `PARTIAL`, `MISSING` or `SKIPPED`. `REVIEWED` requires an `evidence_locator`; every other status requires a specific reason. Do not infer review from file existence. A review may still describe what it could assess, but it cannot emit `READY_FOR_HUMAN_SUBMISSION_CHECK` until every required input is `REVIEWED`.

## Reviewer panel

Evaluate from four independent perspectives:

1. **Handling editor** — desk-reject fit, novelty framing, article type, completeness, policy/compliance.
2. **Domain reviewer** — scientific question, prior-work positioning, mechanism/interpretation, novelty, missing comparisons.
3. **Methods/statistics reviewer** — design, assumptions, sample size, uncertainty, statistical validity, reproducibility, robustness.
4. **Skeptical reviewer** — alternative explanations, overclaiming, hidden confounders, weak figures, unsupported generalization.

Do not average away disagreement. If one reviewer finds a plausible fatal flaw, keep it visible.

## Generate 3–5 substantive comments

Each comment must contain:

- stable id `RS-1`, `RS-2`, ...;
- persona;
- severity: `blocker`, `major`, `minor`;
- exact manuscript location;
- objection in reviewer language;
- evidence for why the objection is likely;
- what would satisfy the reviewer;
- `requires_author_data`: true/false;
- safe revision plan;
- response-to-reviewer draft;
- status: `OPEN` / `RESOLVED` / `AUTHOR_DECISION`.

Do not fill the list with grammar issues. At least 3 comments must concern scientific content, evidence, methods, fit or interpretation.

## Revision loop

Maximum 3 rounds:

1. generate comments;
2. revise only where evidence permits;
3. rerun Claim–Evidence, reference/citation-support, figure/table and compliance checks on changed sections;
4. mark a comment resolved only when the evidence and manuscript change actually address it;
5. if the required remedy is a new experiment/new dataset/new approval/new author statement, stop and mark `AUTHOR_DECISION` or `REQUIRES_AUTHOR_DATA`.

Never invent new results, sample sizes, significance, robustness tests, ethics approvals or supplementary analyses merely to satisfy the simulator.

## Rebuttal discipline

Draft a response using:

- Reviewer Comment
- Response
- Change Made
- Location
- Remaining Limitation (if any)

Use professional disagreement when appropriate. Do not automatically concede a reviewer premise if the manuscript evidence does not support it.

## Cover letter

Only after blocker/major comments are resolved or explicitly accepted by the author, prepare a cover-letter draft grounded in verified manuscript facts and current journal fit. Do not claim novelty priority, exclusivity, ethics status or non-simultaneous submission unless confirmed.

## Output

Write `08-readiness/reviewer-simulation.json`:

```json
{
  "round": 1,
  "journal": "...",
  "review_coverage": [
    {"input_id": "manuscript", "status": "REVIEWED", "evidence_locator": "04-manuscript/manuscript.md", "reason": ""},
    {"input_id": "journal_scope", "status": "REVIEWED", "evidence_locator": "05-editorial/journal-evidence.json", "reason": ""},
    {"input_id": "validation_results", "status": "REVIEWED", "evidence_locator": "03-revalidation/validation-results.json", "reason": ""},
    {"input_id": "citation_identity_support", "status": "REVIEWED", "evidence_locator": "04-manuscript/citation-audit.json", "reason": ""},
    {"input_id": "claim_evidence", "status": "REVIEWED", "evidence_locator": "04-manuscript/claim-map.json", "reason": ""},
    {"input_id": "figure_table", "status": "REVIEWED", "evidence_locator": "04-manuscript/figure-manifest.json", "reason": ""},
    {"input_id": "methods_reporting_compliance", "status": "REVIEWED", "evidence_locator": "audit/methods-compliance.md", "reason": ""}
  ],
  "comments": [],
  "summary": {
    "blockers_open": 0,
    "major_open": 0,
    "minor_open": 0
  },
  "cover_letter_status": "NOT_READY"
}
```

When running inside a FORGE workspace, mirror this ledger into `05-editorial/reviewer-panel.json`. In the human-readable review, include a “What this simulated review did not have” section generated from every non-`REVIEWED` ledger row. Never hide a missing input behind a polished verdict.

Simulated comments are never described as actual peer-review reports and must not be assigned an acceptance probability.
