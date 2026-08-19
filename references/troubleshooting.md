# Troubleshooting

Use this guide when the CLI, a quality gate, or an Agent stage stops. The default policy is conservative: diagnose the missing/invalid artifact rather than silently skipping it.

## `No such file or directory: scripts/.../...py`

The documented compatibility subcommands are part of the repository. First verify the checkout is current:

```bash
git pull
python scripts/check_docs.py
```

If `check_docs.py` reports a missing path, the repository/documentation is inconsistent and should be fixed before continuing.

## Example input is missing

Both names are retained for compatibility:

- `examples/input/sample-modeling-report.tex` — canonical name
- `examples/input/sample-model-report.tex` — compatibility alias used by older documentation

## A gate blocks the run

Inspect the machine-readable gate result:

```bash
cat runs/<name>/gate-results/G3.json
python scripts/gates.py G3 --workdir runs/<name>
```

Do not delete or edit the gate result merely to make the pipeline continue. Fix the upstream artifact or use an explicitly documented degradation path.

## G3 requests rollback to S2

The deterministic CLI cannot perform a scientific rewrite by itself. Regenerate the S2 artifact with the Agent prompt, then resume:

```bash
# Agent produces 02-rewrite/manuscript.rewritten.json
# Agent produces/refreshes 03-assess/assessment.json
python scripts/run_pipeline.py --workdir runs/<name> --stage S3 --no-ai-stub
```

## `--no-ai-stub` says S2/S3 artifact is missing

This is expected behavior. `--no-ai-stub` means **consume real Agent-produced artifacts**; it does not enable an undocumented LLM API client. Produce the required files with:

- `prompts/02-academic-rewrite.md`
- `prompts/03-quality-assessment.md`

Then resume from the appropriate stage.

## `--ai-stub` run finishes but is not submission-ready

Correct. Stub mode is for runtime/testing only. The report must show `DEMO_ONLY_NOT_SUBMISSION_READY` even if deterministic checks contain zero errors.

## LaTeX compile check is skipped

Install a LaTeX distribution that provides `latexmk` or `pdflatex`. Until then, G6 records an explicit degradation. A skipped compile check must never be described as a successful compilation.

## Journal information looks old

`scripts/journals.py` uses a local seed database for deterministic matching. Before submission, reverify current information from official/authoritative sources, especially:

- Aims & Scope / accepted article types
- Journal Impact Factor and year
- quartile/category
- APC / open-access policy
- word/figure/reference limits
- current template and Guide for Authors

## Template is marked degraded/non-official

This is intentional. `scripts/journals/fetch_template.py` does not pretend a bundled skeleton is an official publisher file. Replace the fallback with the current official template before submission.

## `bibtexparser` import error

Install repository dependencies:

```bash
pip install -r requirements.txt
```

The test suite and citation validation require `bibtexparser`.

## Preservation checker fails after a legitimate bug fix

The preservation system is a regression guard. Do not regenerate hashes simply to silence the error. Update the manifest's approved bug-fix list only when the change is intentional, reviewed, and does not alter protected scientific behavior. Run:

```bash
python scripts/check_preservation.py
pytest -q
```

## Need to inspect what actually happened

Use the append-only audit log:

```bash
python scripts/run_pipeline.py --workdir runs/<name> --show-audit
```

Also inspect:

- `gate-results/G1.json` … `G6.json`
- `06-validate/validation-final.json`
- `conversion-report.md`

## A prompt/module exists but the CLI does not run it

The W/P/J extension modules (`08`, `09`, `10`) are Agent modules rather than extra Python stages. Use `prompts/00-extension-router.md` to route general SCI writing, polishing, and submission/journal tasks. The seven-stage CLI remains the math-modeling conversion runtime.
