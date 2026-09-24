---
name: scientific-figure-making
description: >-
  Covers publication-ready matplotlib figures for academic papers, slides, and
  reports—bars, trends, scatter, heatmaps, and multi-panel layouts—with this
  repository’s house style, print/vector export conventions, and parity with
  figures4papers demos. Use when the user is finalizing or creating such figures
  in matplotlib. Do not use for interactive dashboards or web viz (Plotly, Altair,
  Bokeh), exploratory-only plots without a publication target, dominant 3D or
  geographic mapping, or Illustrator/Figma-first infographic workflows.
---

# Scientific figure making

## Local repository gate — mandatory precedence

This is a real, separately triggerable vendored copy of the upstream skill, retained under CC BY-NC 4.0. Read [SOURCE.md](SOURCE.md) before reusing or adapting its text or following an external demo.

Before designing a claim-bearing figure, apply these repository rules in order:

1. Read the repository [figure contract](../../references/figure-contract.md) and create the claim/data/script/output/caption chain.
2. Read the local [figures4papers profile](../../references/figures4papers-profile.md); its `ADAPT`, `REJECT`, and `REFERENCE-ONLY` decisions override conflicting advice below.
3. For method comparisons, uncertainty, robustness, or model-result figures, satisfy [Revalidation](../../references/model-validation-matrix.md) before using the figure in [Grounding](../../references/forge-trace-framework.md). The root [M²SCI skill](../../SKILL.md) remains authoritative for scientific claims.
4. Apply the target journal's current official requirements after they are verified.

**Precedence:** verified data and journal requirements → repository figure contract → repository figures4papers profile → Revalidation/Grounding → this vendored skill and its upstream references.

The following are hard overrides, even where an upstream reference documents a different historical practice:

- Magnitude bars start at zero by default. Never truncate or dynamically tighten a bar axis merely to magnify a difference.
- Do not hide ticks or category labels unless every mark remains unambiguous through direct labels or an equally precise mapping.
- Color is never the only channel. Reject alpha-only categories and red–green-only contrasts; add line style, marker, hatch, outline, or direct labels.
- Design at the final single- or double-column physical size. Fixed ultra-wide canvases are not a default.
- Name every uncertainty interval, sample unit, repetition level, normalization, mask, and transformation. Cross-validation folds are not automatically independent samples.
- Treat exact palettes, demo code, images, paper data, layouts, radar areas, and complex 3D recipes as `REFERENCE-ONLY` unless the local profile explicitly allows an independent implementation.
- The package contains no upstream plotting scripts, images, PDFs, or paper data. Demo URLs are locked to the audited commit; do not silently switch to `main`.

This gate overrides every conflicting recommendation in the bundled API, patterns, demos, design theory, and tutorials.

Open `references/` only as needed; do not preload every file. Start from the table below, then follow links inside the document you opened (and into `figure_*` code via [references/demos.md](references/demos.md)) instead of loading the full reference set up front.

## When to load this skill

- Matplotlib figures for **papers, slides, or reports** that must match **this repo’s publication look** (fonts, palette, spines, legends, export).
- Requests involving **grouped bars, trend lines, heatmaps, multi-panel grids**, or **PDF/SVG/high-DPI** output in a scientific-figure context.
- References to **figures4papers** `figure_*` projects or “same style as the repo figures.”

## When not to load

- **Plotly, Altair, Bokeh**, or other interactive / web-first plotting.
- **EDA-only** plots where seaborn or pandas is enough until there is a publication target.
- Primary workflow is **3D, GIS**, or **non-matplotlib** tooling.
- **Illustrator / Figma–first** layout or infographic (not matplotlib data plots).

## Related files

| File | Open when |
|------|-----------|
| [references/tutorials.md](references/tutorials.md) | End-to-end walkthroughs (bar, trends, heatmap) |
| [references/api.md](references/api.md) | Function signatures, `PALETTE`, validation rules |
| [references/common-patterns.md](references/common-patterns.md) | Layout patterns, legend panel, print-safe bars |
| [references/design-theory.md](references/design-theory.md) | Typography, export policy, palette rationale |
| [references/demos.md](references/demos.md) | Canonical `figure_*` demo links in figures4papers |

