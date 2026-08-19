from __future__ import annotations

import json
from pathlib import Path

from readiness.pipeline_bridge import resolve_inputs, run_from_workdir


def _dump(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_resolve_inputs_uses_existing_pipeline_artifacts(tmp_path):
    wd = tmp_path / "paper"
    _dump(wd / "02-rewrite" / "manuscript.rewritten.json", {"meta": {}, "sections": []})
    (wd / "05-template" / "build").mkdir(parents=True, exist_ok=True)
    (wd / "05-template" / "build" / "references.bib").write_text("", encoding="utf-8")
    (wd / "05-template" / "build" / "main.tex").write_text("\\documentclass{article}", encoding="utf-8")
    _dump(wd / "04-journals" / "journal-match.json", {
        "recommendations": [{"name": "Example Journal", "journal_id": "example", "issn": "1234-5678"}]
    })

    resolved = resolve_inputs(str(wd))
    assert resolved["ir"].endswith("02-rewrite/manuscript.rewritten.json")
    assert resolved["bib"].endswith("05-template/build/references.bib")
    assert resolved["journal_name"] == "Example Journal"
    assert resolved["issn"] == "1234-5678"
    assert resolved["build_tex"].endswith("05-template/build/main.tex")


def test_missing_network_or_official_evidence_becomes_blocker_not_crash(tmp_path):
    wd = tmp_path / "paper"
    _dump(wd / "06-validate" / "validation-final.json", {
        "summary": {"error_count": 0, "unresolved_error_ids": []},
        "checkers": [],
        "verdict": "PASS",
    })
    result = run_from_workdir(str(wd))
    assert result["status"] == "BLOCKED"
    assert (wd / "08-readiness" / "readiness-run.json").is_file()
    assert (wd / "08-readiness" / "reference-verification.json").is_file()
    assert (wd / "08-readiness" / "journal-fit.json").is_file()
    assert any(x["code"] == "ARTIFACT_MISSING" for x in result["blockers"])
