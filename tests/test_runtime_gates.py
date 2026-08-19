from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = REPO_ROOT / "examples" / "input" / "sample-modeling-report.tex"
RUNNER = REPO_ROOT / "scripts" / "run_pipeline.py"


def _run(*args: str):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_failed_g3_blocks_before_journal_matching(tmp_path):
    workdir = tmp_path / "low-score"
    proc = _run(
        "--input", str(SAMPLE),
        "--workdir", str(workdir),
        "--score", "4.0",
        "--stop-after", "S4",
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    gate = json.loads((workdir / "gate-results" / "G3.json").read_text(encoding="utf-8"))
    assert gate["passed"] is False
    assert not (workdir / "04-journals" / "journal-match.json").exists()
    events = [json.loads(line) for line in (workdir / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(e.get("result") == "blocked" and e.get("gate") == "G3" for e in events)


def test_dry_run_respects_pipeline_stage_limit(tmp_path):
    workdir = tmp_path / "dry"
    proc = _run(
        "--input", str(SAMPLE),
        "--workdir", str(workdir),
        "--mode", "dry-run",
        "--score", "7.2",
        "--scope-tags", "applied-mathematics,mathematical-modelling,optimization",
        "--method-tags", "ode-pde,numerical-simulation,optimization",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (workdir / "04-journals" / "journal-match.json").exists()
    assert not (workdir / "05-template" / "build" / "main.tex").exists()


def test_no_ai_stub_requires_real_agent_artifacts(tmp_path):
    workdir = tmp_path / "real-mode"
    proc = _run(
        "--input", str(SAMPLE),
        "--workdir", str(workdir),
        "--no-ai-stub",
        "--stop-after", "S2",
    )
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "real S2 artifact" in combined
