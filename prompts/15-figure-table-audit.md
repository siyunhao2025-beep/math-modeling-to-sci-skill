# S8.4 — Figure & Table Scientific Review

## Objective

Review every figure/table as evidence, not decoration. A figure that exists and compiles can still mislead a reviewer.

Run `scripts/readiness/figure_table_audit.py` first, then visually/scientifically inspect every object.

## Figure checklist

For every figure:

- source file exists and matches the cited figure number;
- axes are named, units are present, tick ranges are sensible;
- color/line/marker encoding is unambiguous and accessible;
- legends identify every series/category;
- error bars / shaded uncertainty are defined in the caption or methods;
- log/normalized/standardized scales are explicitly disclosed;
- smoothing/interpolation/filtering is disclosed where relevant;
- zero lines, significance marks and reference lines are explained;
- map projections, coordinates, altitude/latitude/local-time conventions are clear when applicable;
- no cropping, axis truncation or scale choice visually exaggerates the claimed effect;
- panel labels and cross-references are correct;
- caption is self-contained enough for a reviewer to interpret the evidence;
- numerical/qualitative claims in Results agree with what the figure actually shows.

## Table checklist

For every table:

- headers, units, significant digits and uncertainty notation are consistent;
- sample size / denominator is clear where applicable;
- missing values and abbreviations are defined;
- rounding does not create false disagreement with text/figures;
- statistics reported in the table match Methods definitions;
- every table is cited in text and every material table claim is traceable;
- no duplicated table/figure communicates conflicting values.

## Severity

- `BLOCKER`: missing source, wrong mapping, inconsistent values, misleading scale, undefined uncertainty central to a claim, figure/table contradicts text.
- `MAJOR`: insufficient caption, ambiguous encoding, missing unit, statistical annotation unclear.
- `MINOR`: typography/alignment/visual polish with no scientific consequence.

## Output

Update `08-readiness/figure-table-audit.json` with:

- `visual_scientific_review`: `PASS`, `PASS_WITH_WARNINGS`, or `FAIL`;
- per-object `scientific_findings`;
- `text_consistency_findings`;
- `required_repairs`;
- `author_decisions` where a repair would alter protected scientific content.

Do not redraw or simplify a scientific figure in a way that changes its underlying data or information relationships without author approval.
