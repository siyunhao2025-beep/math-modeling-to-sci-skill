from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_checker():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_preservation.py"
    spec = importlib.util.spec_from_file_location("check_preservation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_distribution_contract_passes():
    root = Path(__file__).resolve().parents[1]
    checker = _load_checker()
    manifest = root / "config" / "preservation-manifest.json"
    errors, details = checker.verify(root, manifest)
    assert errors == []
    assert "history_mode" in details


def test_skill_entrypoint_matches_reviewed_contract():
    root = Path(__file__).resolve().parents[1]
    checker = _load_checker()
    manifest = root / "config" / "preservation-manifest.json"
    data = __import__("json").loads(manifest.read_text(encoding="utf-8"))
    skill = (root / "SKILL.md").read_bytes()
    n = int(data["skill_contract"]["bytes"])
    assert checker.sha256_bytes(skill[:n]) == data["skill_contract"]["sha256"]
