# S8.6 — One-click Submission Preflight

## Objective

Perform a final, integrated pre-submission audit that refuses to hide unresolved blockers.

Run:

```bash
python scripts/readiness/submission_preflight.py --workdir <workdir>
```

The command aggregates S6 and S8 artifacts. Before running it, ensure the Agent-level semantic audits have been written back to their JSON files.

## Mandatory blocker classes

Do not release a paper for human submission check when any of these remain:

- unresolved S6 error;
- LaTeX compile check missing/skipped/failed for a LaTeX submission;
- unverified/conflicting reference;
- citation that contradicts or does not support the claim;
- unsupported high-risk claim;
- key conclusion without evidence traceability;
- missing/mismapped figure/table or failed visual scientific review;
- current official Aims & Scope/article type not verified;
- unresolved ethics/consent/data/COI requirement;
- relevant reporting guideline not reviewed;
- unresolved simulated-review blocker/major comment;
- LaTeX manuscript lacking verified official-template provenance.

## Output statuses

Use exactly:

- `BLOCKED`
- `AUTHOR_ACTION_REQUIRED`
- `READY_FOR_HUMAN_SUBMISSION_CHECK`

Never output “acceptance-ready,” “guaranteed submission-ready,” or an acceptance probability.

## Human handoff package

When status reaches `READY_FOR_HUMAN_SUBMISSION_CHECK`, present:

1. final manuscript path;
2. clean verified BibTeX path;
3. target journal + article type + official evidence date;
4. S6 validation summary;
5. reference/citation-support summary;
6. claim–evidence traceability summary;
7. figure/table audit summary;
8. reporting/methods/ethics summary;
9. reviewer simulator summary;
10. template provenance + compile status;
11. preflight JSON/Markdown paths;
12. remaining non-blocking author choices.

## Submission truthfulness

The preflight reduces preventable desk-reject/reviewer risks. It does not know the editor's unpublished preferences and cannot guarantee peer-review outcome.
