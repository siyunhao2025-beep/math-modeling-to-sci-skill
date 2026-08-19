# Open-source Skill / Prompt Survey and Integration Provenance

**Snapshot date:** 2026-08-19  
**Purpose:** document the GitHub research used for the additive SCI writing / polishing / submission extension.

> Star counts are a point-in-time snapshot and will change. They are included only as a community-adoption signal,
> not as a quality guarantee.

## Candidate repositories

| Repository | Stars (snapshot) | License status | Main reusable capability | Integration decision |
|---|---:|---|---|---|
| `binary-husky/gpt_academic` | 71,201 | GPL-3.0 | Full-project LaTeX polishing/proofreading, command & math protection, safe chunking/reassembly, diff-oriented workflow | **Concept only.** No GPL code/prompt text copied into this MIT repository. |
| `ahmetbersoz/chatgpt-prompts-for-academic-writing` | 4,895 | No declared license in GitHub metadata at survey time | Academic-writing prompt taxonomy: research planning, literature review, language/style improvement | **Concept only.** No source text copied because reuse terms are unclear. |
| `zLanqing/codex-claude-academic-skills` | 3,002 | MIT | Research writing/polishing, evidence-aware revision, preservation of formulas/terms/citations, reviewer-response workflow | **Generalized and reimplemented** in Modules W/P/J. Domain-specific assumptions removed. |
| `HughYau/AcademicForge` | 2,466 | GitHub metadata reports non-standard/NOASSERTION | Curated research-skill architecture and publication-guideline awareness | **Concept only.** Used as architecture signal, not copied. |
| `aipoch/medical-research-skills` | 1,730 | MIT | Target-journal matching, cover-letter workflow, point-by-point reviewer response and traceable change locations | **Generalized and reimplemented** in Module J; medical-specific scoring/examples removed. |
| `lishix520/academic-paper-skills` | 1,187 | MIT | Strategist → composer workflow, plan-first writing, phase/section quality gates, reviewer-perspective self-check | **Generalized and reimplemented** in Module W. |
| `AIScientists-Dev/academic-humanizer` | 1,031 | Repository LICENSE is MIT | Natural scholarly voice, evidence-linked claims, removal of repetitive AI-style prose without weakening scientific precision | **Generalized and reimplemented** in Module P. |

## What was added

### 1. SCI paper writing — `prompts/08-sci-writing.md`
Adds:
- source ledger before drafting;
- problem → gap → approach → evidence → contribution chain;
- section-specific rhetorical moves;
- result `Claim → Evidence → Quantification → Boundary`;
- discussion `Observation → Interpretation → Mechanism → Alternatives → Limitation`;
- multi-round literature/gap validation;
- reviewer-perspective five-dimension self-check.

Primary inspiration:
- `lishix520/academic-paper-skills` (MIT);
- `zLanqing/codex-claude-academic-skills` (MIT);
- high-level prompt taxonomy from `ahmetbersoz/...` (concept only).

### 2. Language polishing — `prompts/09-language-polish.md`
Adds:
- three polishing depths;
- protected-span lock for LaTeX, equations, citations, numbers and units;
- scientific claim-strength freeze;
- calibrated hedging;
- topic–stress / old→new information flow;
- anti-boilerplate academic style;
- long-LaTeX-project chunk → polish → reassemble → diff audit workflow.

Primary inspiration:
- `binary-husky/gpt_academic` (concept only because GPL);
- `zLanqing/codex-claude-academic-skills` (MIT);
- `AIScientists-Dev/academic-humanizer` (MIT).

### 3. Journal search & submission — `prompts/10-submission-journal-search.md`
Adds:
- manuscript profile;
- evidence-backed journal shortlist;
- live verification cards;
- 100-point scope/method/evidence/audience/practical-fit framework;
- current Guide for Authors compliance matrix;
- cover-letter and declarations workflow;
- pre-submission preflight;
- resubmission strategy;
- reviewer-response traceability.

Primary inspiration:
- `aipoch/medical-research-skills` (MIT);
- existing local S4–S7 workflow;
- publication-guideline concepts observed across curated skill repositories.

## Conflict-resolution decisions

The integration deliberately **does not replace** the existing seven-stage math-modeling pipeline.

- Existing S1–S7 remains the canonical conversion workflow.
- New modules are routed only when the user asks for general SCI writing, polishing, or journal/submission work, or as an additive step after the legacy pipeline.
- If new journal/style advice conflicts with the original mathematical content, original scientific content wins.
- If a target journal's current official rule conflicts with a local default format rule, the official rule wins **only for presentation/formatting**, never for data, equations, conclusions or evidence.

## License / provenance policy

This repository remains MIT.

- MIT-source workflows were **reimplemented and generalized**, not vendored wholesale.
- GPL, no-license, or unclear-license repositories were used only to identify workflow ideas; no code, template, or substantial prompt text was copied.
- Repository names are retained here for provenance and reproducibility of the research step.

## Preservation design

The integration is additive:
- all pre-existing repository files except `SKILL.md` are SHA-256 protected;
- the entire original `SKILL.md` is preserved byte-for-byte as the prefix of the updated file;
- new content is appended after a clearly marked extension boundary;
- `config/preservation-manifest.json` records the baseline hashes;
- `scripts/check_preservation.py` and `tests/test_preservation_contract.py` verify the contract.

This means the original mathematical-modeling logic, assets, prompts, schemas, examples and tests remain unchanged.
