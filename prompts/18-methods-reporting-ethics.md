# S8.7 — Reporting Guidelines, Methods/Statistics & Ethics Compliance

## Objective

Turn vague “methodological rigor” into explicit, field-appropriate checks and catch submission-policy omissions before the editor does.

Run `scripts/readiness/compliance_audit.py` first. Treat its output as a pre-screen, not certification.

## A. Reporting guideline selection

Based on the actual study design, identify relevant guideline families such as:

- PRISMA — systematic reviews/meta-analyses;
- STROBE — observational studies;
- TRIPOD — prediction/prognostic/diagnostic model reporting;
- ARRIVE — in vivo animal research;
- CONSORT — randomized trials;
- STARD — diagnostic accuracy studies.

At execution time, verify the **current official checklist/version** and record source + retrieval date. Do not copy an outdated local checklist and call it current.

For every applicable checklist item classify:

- `PASS`
- `MISSING`
- `NOT_APPLICABLE`
- `AUTHOR_CHECK`

A missing mandatory item is a blocker or major issue depending on journal policy.

## B. Statistics/methodology hard checks

Assess, when applicable:

- study design and inclusion/exclusion criteria;
- sample-size rationale / power / event-per-variable adequacy;
- randomization, allocation, blinding/masking;
- preprocessing and missing-data handling;
- test assumptions and model assumptions;
- exact p-value/reporting convention;
- effect sizes and uncertainty intervals;
- multiple-testing control;
- error-bar definition;
- sensitivity/robustness analysis;
- train/validation/test separation and leakage risk for ML;
- hyperparameter tuning disclosure;
- external validation / calibration for prediction models;
- code/software version, random seed and reproducibility;
- limitations created by data coverage or sampling geometry.

Do not mark a test “passed” because the manuscript contains the word “significant.” Require the actual reported evidence.

## C. Ethics and publication declarations

Check applicability and presence of:

- ethics/IRB/IACUC or equivalent approval;
- approval number only if author/source confirmed;
- informed consent / waiver when applicable;
- data availability;
- code availability where custom code materially supports the work;
- conflict of interest / competing interests;
- funding;
- author contributions if journal requires;
- AI-use disclosure if journal/publisher policy requires;
- trial registration / protocol registration where applicable.

Never invent approval IDs, consent status, funding grants, author contributions or conflict statements.

## D. Reproducibility package

If data/code/supplements exist, prepare an audit-ready manifest:

- artifact name;
- version/hash;
- repository/DOI/URL;
- access conditions;
- license if known;
- manuscript section that depends on it;
- whether anonymization/blinding is required for review.

If sharing is restricted, state the restriction truthfully and identify what the target journal requires.

## Output

Update `08-readiness/compliance-audit.json` with:

- verified reporting-guideline status;
- detailed statistics/methods findings;
- ethics/declaration findings;
- reproducibility manifest;
- blocker/major/minor counts;
- exact author actions required.
