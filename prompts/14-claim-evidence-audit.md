# S8.3 — Claim–Evidence Audit

## Objective

Make every material scientific claim traceable to actual evidence before submission.

Run `scripts/readiness/claim_evidence.py` first. Then review each generated claim semantically.

## Claim classes

Use exactly one primary class:

- `OBSERVATION_OR_RESULT`
- `QUANTITATIVE_RESULT`
- `COMPARATIVE_RESULT`
- `ESTABLISHED_KNOWLEDGE`
- `INTERPRETATION`
- `MECHANISM_HYPOTHESIS`
- `CAUSAL_CLAIM`
- `METHOD_PERFORMANCE`
- `LIMITATION`
- `GENERALIZATION`

## Evidence classes

Map each claim to one or more:

- source dataset / original manuscript value;
- figure;
- table;
- equation/model derivation;
- statistical test;
- verified external citation;
- author-confirmed statement;
- none.

For each claim set `agent_semantic_status`:

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `UNSUPPORTED`
- `CONTRADICTED`
- `OUT_OF_SCOPE_GENERALIZATION`
- `AUTHOR_CHECK`

## Hard blockers

Block release when:

- a precise number has no traceable data/table/figure/source;
- a causal claim has only correlational evidence;
- a mechanism is stated as directly observed when it was inferred;
- a conclusion is broader than the analyzed population/time/space/model domain;
- a method-performance statement lacks the comparison/test it claims;
- an uncertainty/significance claim is not backed by the stated statistic;
- a key conclusion is not supported by any result-level evidence.

## Repair rules

Prefer the smallest truthful repair:

1. attach the missing evidence link if it already exists;
2. narrow the wording to the supported scope;
3. convert causal/mechanistic wording to calibrated interpretation when direct evidence is absent;
4. move unsupported speculation to a clearly labeled hypothesis/limitation;
5. if new experiment/data are genuinely required, mark `REQUIRES_AUTHOR_DATA`; never invent them.

Never change protected numbers, equations, figure/table data or core conclusions merely to make the audit pass. If evidence genuinely contradicts a protected conclusion, raise `[[AUTHOR_CHECK: EVIDENCE_CONFLICT]]`.

## Output

Update `08-readiness/claim-evidence-audit.json` without deleting deterministic fields. Add:

- `agent_semantic_summary`;
- per-claim `agent_semantic_status`, `evidence_map`, `reason`, `repair`;
- `semantic_blockers`;
- `key_conclusion_traceability`.
