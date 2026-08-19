# Architecture

This document describes the **implemented** runtime architecture. It deliberately separates deterministic Python behavior from Agent/LLM behavior so that documentation does not imply capabilities the CLI does not have.

## 1. Two execution layers

### Deterministic Python runtime

`scripts/run_pipeline.py` executes the mechanical parts of S1–S7:

- S1: parse source files into manuscript IR;
- S4: score the local journal seed pool;
- S5: render a fallback LaTeX build;
- S6: run deterministic validation checks;
- S7: assemble a conservative conversion report;
- after S1–S6: call `scripts/gates.py` to evaluate the configured gate.

The runtime loads `config/pipeline.yaml` for mode/stage behavior and `config/quality-gates.yaml` for gate conditions and failure policy.

### Agent/LLM layer

S2 (academic rewriting) and S3 (independent quality assessment) are reasoning tasks. The Python CLI does **not** contain a hidden LLM client.

- `--ai-stub` is a demo path only. It passes the IR through at S2 and creates a schema-valid placeholder S3 assessment. The report is marked `DEMO_ONLY_NOT_SUBMISSION_READY`.
- `--no-ai-stub` consumes real `02-rewrite/manuscript.rewritten.json` and `03-assess/assessment.json` artifacts already produced by the Agent Skill. If either artifact is missing, the CLI stops with an explicit error.

This separation prevents a deterministic test harness from being mistaken for real scientific rewriting or peer review.

## 2. Canonical S1–S7 flow

```text
source
  ↓
S1 parse ──G1──▶ S2 agent rewrite ──G2──▶ S3 agent assessment ──G3──▶
S4 journal match ──G4──▶ S5 render ──G5──▶ S6 validate ──G6──▶ S7 report
```

Each gate writes `gate-results/Gx.json`. An error-severity condition that is not evaluable is **not silently treated as PASS**. A condition explicitly configured as skippable may be recorded as skipped/degraded.

## 3. Gate behavior

`config/quality-gates.yaml` remains the policy source. `scripts/gates.py` implements the named checks and produces a machine-readable condition-by-condition result.

`run_pipeline.py` handles configured actions conservatively:

- `retry`: rerun a deterministic stage when retrying can change the result;
- `degrade`: continue only with an explicit audit event/disclosure;
- `block`: stop the pipeline and, where possible, produce a diagnostic report;
- `rollback`: for semantic S2/S3 work, stop and tell the Agent/author which upstream artifact must be regenerated rather than pretending the CLI can rewrite science;
- `ask_human`: pause in interactive mode; use the configured fallback in auto mode.

G6 is the hard submission-readiness gate. A demo/stub run is never labeled submission-ready even if deterministic checks happen to contain zero errors.

## 4. Run modes

- `auto`: execute the requested stage range and apply configured gate actions automatically.
- `interactive`: pause after gates and at human checkpoints; requires a TTY.
- `dry-run`: according to `config/pipeline.yaml`, stop no later than S4 and do not render a submission build.

Useful commands:

```bash
python scripts/run_pipeline.py --input examples/input/sample-modeling-report.tex --workdir runs/demo --mode dry-run
python scripts/run_pipeline.py --workdir runs/demo --stage S3 --stop-after S4 --no-ai-stub
python scripts/run_pipeline.py --workdir runs/demo --show-audit
python scripts/gates.py G6 --workdir runs/demo
```

## 5. Intermediate representation and artifacts

The manuscript IR is defined by `config/schema/manuscript.schema.json`. Stages exchange on-disk artifacts rather than relying on conversational memory. Important outputs include:

- `01-parse/manuscript.ir.json`
- `02-rewrite/manuscript.rewritten.json`
- `03-assess/assessment.json`
- `04-journals/journal-match.json`
- `05-template/build/`
- `06-validate/validation-final.json`
- `gate-results/G1.json` … `G6.json`
- `conversion-report.md`
- `audit.jsonl`

## 6. Compatibility command layout

The implementation keeps the original flat modules (`scripts/ingest.py`, `validate.py`, `journals.py`, `render.py`, `report.py`) and also provides the subcommands referenced by the documentation and `pipeline.yaml`, such as:

- `scripts/ingest/parse_latex.py`
- `scripts/validate/check_citations.py`
- `scripts/journals/match_journals.py`
- `scripts/render/render_latex.py`
- `scripts/report/build_report.py`

The subcommands are thin compatibility wrappers around the canonical modules, not duplicate implementations.

## 7. Integrated SCI extension modules

The W/P/J modules are **Agent modules, not additional Python pipeline stages**:

- W — `prompts/08-sci-writing.md`
- P — `prompts/09-language-polish.md`
- J — `prompts/10-submission-journal-search.md`

They are routed by `prompts/00-extension-router.md` and load `prompts/shared/05-integrity-preservation.md`. They may be used independently for non-modeling manuscripts. In that independent mode there may be no manuscript IR, so preservation is enforced by explicit protected-span/source-ledger checks rather than by pretending the S1–S7 Python gates automatically ran.

## 8. Preservation and integrity

`config/preservation-manifest.json` plus `scripts/check_preservation.py` are a **compatibility regression guard**, not a security or anti-tamper system. The checker protects the original `SKILL.md` legacy prefix, verifies required paths, and—when Git history is available—limits changes to legacy files to an explicit approved bug-fix allowlist.

Scientific-content preservation during an actual manuscript task is a separate concern and is governed by the IR, source ledger, G2/G6 checks, and `shared/05-integrity-preservation.md`.

## 9. Known boundaries

- Current journal seed matching is offline/deterministic; IF, quartile, APC, scope, and author guidelines must be reverified online before submission.
- Bundled templates are fallbacks, not publisher originals.
- A missing LaTeX toolchain causes an explicit compile-check degradation; it is never reported as a successful compilation.
- The CLI does not create novel scientific evidence, run new experiments, or guarantee journal acceptance.
