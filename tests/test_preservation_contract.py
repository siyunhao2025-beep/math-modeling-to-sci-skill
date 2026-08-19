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


def test_preintegration_files_are_unchanged():
    root = Path(__file__).resolve().parents[1]
    checker = _load_checker()
    manifest = root / "config" / "preservation-manifest.json"
    assert checker.verify(root, manifest) == []
