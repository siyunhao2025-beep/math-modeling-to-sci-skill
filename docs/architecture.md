# Architecture

This document describes the **implemented** runtime architecture. It deliberately separates deterministic Python behavior from Agent/LLM behavior so that documentation does not imply capabilities the CLI does not have.

## 1. Three execution layers

### A. Deterministic S1–S7 Python runtime

`scripts/run_pipeline.py` executes the mechanical parts of the legacy S1–S7 workflow:

- S1: parse source files into manuscript IR;
- S4: score the local journal seed pool;
- S5: render a fallback LaTeX build;
- S6: run deterministic validation checks;
- S7: assemble a conservative conversion report;
- after S1–S6: call `scripts/gates.py` to evaluate the configured gate.

The runtime loads `config/pipeline.yaml` for mode/stage behavior and `config/quality-gates.yaml` for gate conditions and failure policy.

### B. Agent/LLM reasoning layer

S2 (academic rewriting) and S3 (independent quality assessment) are reasoning tasks. The Python CLI does **not** contain a hidden LLM client.

- `--ai-stub` is a demo path only. It passes the IR through at S2 and creates a schema-valid placeholder S3 assessment. The report is marked `DEMO_ONLY_NOT_SUBMISSION_READY`.
- `--no-ai-stub` consumes real `02-rewrite/manuscript.rewritten.json` and `03-assess/assessment.json` artifacts already produced by the Agent Skill. If either artifact is missing, the CLI stops with an explicit error.

W/P/J and the semantic portions of S8 are also Agent tasks.

### C. Post-S6 Publication Readiness Suite (S8 logical layer)

S8 is a **logical post-S6 layer**, not a renumbering of `config/pipeline.yaml`. It combines deterministic readiness utilities under `scripts/readiness/` with explicit Agent semantic review.

Deterministic parts include:

- DOI/reference identity verification via Crossref + Semantic Scholar/PubMed corroboration;
- recent-journal-content retrieval and reproducible lexical fit baseline;
- claim/evidence structural ledger;
- figure/table source/mapping checks;
- reporting/methods/ethics pre-screen;
- optional LanguageTool diagnostics;
- advisory similar-paper discovery;
- official-template provenance download/manifest;
- aggregated submission preflight.

Agent-only semantic parts include:

- whether a cited paper actually supports the specific manuscript claim;
- whether a claim is scientifically supported rather than merely linked to an object;
- visual/scientific interpretation of figures and tables;
- current official journal scope/article-type interpretation;
- field-specific reporting-checklist completion;
- Reviewer Simulator and revision/rebuttal loop.

## 2. Canonical flow

Legacy runtime:

```text
source
  ↓
S1 parse ──G1──▶ S2 agent rewrite ──G2──▶ S3 agent assessment ──G3──▶
S4 journal match ──G4──▶ S5 render ──G5──▶ S6 validate ──G6──▶ S7 report
```

Publication-oriented execution:

```text
S1 → S2 → S3 → S4 → S5 → S6
                         ↓
                  S8 readiness suite
                         ↓
              final report / package
```

The S8 preflight is the stronger submission-facing authority. Passing S6 alone means runtime validation passed; it does **not** mean the reference reality layer, deep journal fit, Claim–Evidence audit, visual review, ethics/reporting checks and simulated peer-review risks were cleared.

## 3. Gate behavior

`config/quality-gates.yaml` remains the S1–S6 policy source. `scripts/gates.py` implements the named checks and produces a machine-readable condition-by-condition result.

`run_pipeline.py` handles configured actions conservatively:

- `retry`: rerun a deterministic stage when retrying can change the result;
- `degrade`: continue only with an explicit audit event/disclosure;
- `block`: stop the pipeline and, where possible, produce a diagnostic report;
- `rollback`: for semantic S2/S3 work, stop and tell the Agent/author which upstream artifact must be regenerated rather than pretending the CLI can rewrite science;
- `ask_human`: pause in interactive mode; use the configured fallback in auto mode.

G6 is the hard **legacy runtime validation gate**. The S8 submission-facing blocker policy lives in `config/publication-readiness.yaml` and is aggregated by `scripts/readiness/submission_preflight.py`.

## 4. Run modes

- `auto`: execute the requested legacy stage range and apply configured gate actions automatically.
- `interactive`: pause after legacy gates and at human checkpoints; requires a TTY.
- `dry-run`: according to `config/pipeline.yaml`, stop no later than S4 and do not render a submission build.

Useful legacy commands:

```bash
python scripts/run_pipeline.py --input examples/input/sample-modeling-report.tex --workdir runs/demo --mode dry-run
python scripts/run_pipeline.py --workdir runs/demo --stage S3 --stop-after S4 --no-ai-stub
python scripts/run_pipeline.py --workdir runs/demo --show-audit
python scripts/gates.py G6 --workdir runs/demo
```

Useful S8 commands:

```bash
python scripts/readiness/reference_verifier.py --bib references.bib --out runs/demo/08-readiness/reference-verification.json --clean-bib runs/demo/08-readiness/references.clean.bib
python scripts/readiness/claim_evidence.py --ir runs/demo/02-rewrite/manuscript.rewritten.json --out runs/demo/08-readiness/claim-evidence-audit.json
python scripts/readiness/figure_table_audit.py --ir runs/demo/02-rewrite/manuscript.rewritten.json --out runs/demo/08-readiness/figure-table-audit.json
python scripts/readiness/compliance_audit.py --manuscript runs/demo/02-rewrite/manuscript.rewritten.json --out runs/demo/08-readiness/compliance-audit.json
python scripts/readiness/submission_preflight.py --workdir runs/demo
```

`run_readiness.py` can execute the deterministic S8 checks in one command once the target-journal evidence inputs are prepared.

## 5. Intermediate representation and artifacts

The manuscript IR is defined by `config/schema/manuscript.schema.json`. Stages exchange on-disk artifacts rather than relying on conversational memory. Important legacy outputs include:

- `01-parse/manuscript.ir.json`
- `02-rewrite/manuscript.rewritten.json`
- `03-assess/assessment.json`
- `04-journals/journal-match.json`
- `05-template/build/`
- `06-validate/validation-final.json`
- `gate-results/G1.json` … `G6.json`
- `conversion-report.md`
- `audit.jsonl`

Important S8 outputs live under `08-readiness/`:

- `reference-verification.json`
- `references.clean.bib`
- `citation-support-audit.json`
- `journal-fit.json`
- `claim-evidence-audit.json`
- `figure-table-audit.json`
- `compliance-audit.json`
- `reviewer-simulation.json`
- optional `language-audit.json`
- optional `similarity-precheck.json`
- `template-provenance.json` for LaTeX official-template checks
- `submission-preflight.json`
- `submission-preflight.md`

## 6. Reference reality layer

`scripts/readiness/reference_verifier.py` treats Crossref as the primary DOI bibliographic source and uses Semantic Scholar/PubMed as independent corroboration when available. Network failures or provider absence remain unverified/unknown; they are never silently treated as PASS.

The resulting clean BibTeX is strict by default: API-unverified/conflicting entries are excluded. This verifies bibliographic identity only. Contextual claim support is a separate Agent audit using `prompts/12-reference-depth-audit.md`.

Provider provenance is documented in `references/publication-readiness-api-sources.md`.

## 7. Deep journal fit

`scripts/readiness/journal_fit.py` intentionally does not scrape arbitrary publisher HTML. The Agent first verifies current official Aims & Scope/article-type pages and writes those texts/provenance as inputs. Crossref then provides recent published/online journal records as an auditable corpus baseline.

The deterministic score is a reproducible lexical baseline, not a semantic editorial-fit score. `prompts/13-journal-fit-deep.md` performs the actual semantic scope/audience/article-type risk review.

## 8. Claim/evidence, figures and compliance

- `claim_evidence.py` identifies claim-like sentences and explicit evidence links. The Agent then determines whether the evidence genuinely supports each claim.
- `figure_table_audit.py` checks source/caption/mapping/in-text-reference integrity. The Agent visually reviews axes, units, uncertainty, scale choices, captions and text agreement.
- `compliance_audit.py` recommends reporting-guideline families and flags high-level statistics/ethics/data/COI/funding gaps. Current official guideline versions must be verified at runtime.

## 9. Reviewer Simulator

`prompts/16-reviewer-simulator.md` creates 3–5 substantive likely objections from handling-editor, domain-reviewer, methods/statistics and skeptical-reviewer perspectives. Comments are structured, location-specific and revision-oriented. New experiments/data are never fabricated to satisfy the simulation.

The output is validated against `config/schema/reviewer-simulation.schema.json` when used in a strict workflow. Simulated comments are never represented as actual peer-review reports or converted into acceptance probabilities.

## 10. Submission preflight

`scripts/readiness/submission_preflight.py` aggregates S6 + S8 artifacts. It emits only:

- `BLOCKED`
- `AUTHOR_ACTION_REQUIRED`
- `READY_FOR_HUMAN_SUBMISSION_CHECK`

For LaTeX builds it requires a successful compile checker and verified official-template provenance. Word/non-LaTeX submissions do not receive a meaningless LaTeX-compile blocker.

`report.py` treats S8 preflight as authoritative when present. An S6 pass without S8 is labeled `S6_PASSED_S8_NOT_RUN`, not full readiness.

## 11. Compatibility command layout

The implementation keeps the original flat modules (`scripts/ingest.py`, `validate.py`, `journals.py`, `render.py`, `report.py`) and also provides the subcommands referenced by the documentation and `pipeline.yaml`, such as:

- `scripts/ingest/parse_latex.py`
- `scripts/validate/check_citations.py`
- `scripts/journals/match_journals.py`
- `scripts/render/render_latex.py`
- `scripts/report/build_report.py`

The subcommands are thin compatibility wrappers around the canonical modules, not duplicate implementations.

## 12. Integrated SCI extension modules

The W/P/J modules are Agent modules:

- W — `prompts/08-sci-writing.md`
- P — `prompts/09-language-polish.md`
- J — `prompts/10-submission-journal-search.md`

S8 modules are routed through `prompts/11-publication-readiness-orchestrator.md` and `prompts/12`–`18`.

All extension modules load `prompts/shared/05-integrity-preservation.md`. When there is no manuscript IR, preservation is enforced by protected-span/source-ledger checks rather than by pretending S1–S7 gates ran.

## 13. Preservation and integrity

`config/preservation-manifest.json` plus `scripts/check_preservation.py` are a **compatibility regression guard**, not a security or anti-tamper system. The checker protects the original `SKILL.md` legacy prefix, verifies required paths, and—when Git history is available—limits changes to legacy files to an explicit approved bug-fix allowlist.

Scientific-content preservation during an actual manuscript task is governed by the IR, source ledger, G2/G6 checks, S8 Claim–Evidence/visual audits and `shared/05-integrity-preservation.md`.

## 14. Known boundaries

- No public metadata API proves contextual citation support; semantic support must be audited separately.
- No generic API can reliably identify every journal's “accepted articles”; Crossref recent records are described as published/online unless an official journal source explicitly says accepted/in press.
- The advisory Semantic Scholar similarity precheck is not iThenticate/Turnitin or a plagiarism percentage.
- LanguageTool is optional and no public endpoint is assumed by default.
- Official journal template status is provenance-based and must be verified from the current official journal/publisher source.
- The system cannot create new scientific evidence, run missing experiments, fabricate ethics approvals, or guarantee journal acceptance.
