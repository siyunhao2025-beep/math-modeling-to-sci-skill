from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_checker():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_preservation.py"
    spec = importlib.util.spec_from_file_location("check_preservation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, checker, contract: bytes) -> Path:
    manifest = {
        "schema_version": "3.0",
        "baseline_commit": None,
        "extension_baseline_commit": None,
        "skill_contract": {
            "path": "SKILL.md",
            "bytes": len(contract),
            "sha256": checker.sha256_bytes(contract),
        },
        "required_paths_without_git_history": ["SKILL.md"],
        "required_extension_paths": [],
        "preservation_reasons": {},
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


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
    data = json.loads(manifest.read_text(encoding="utf-8"))
    skill = checker.normalize_newlines((root / "SKILL.md").read_bytes())
    n = int(data["skill_contract"]["bytes"])
    assert checker.sha256_bytes(skill[:n]) == data["skill_contract"]["sha256"]


def test_crlf_skill_contract_is_accepted(tmp_path):
    checker = _load_checker()
    repo = tmp_path / "repo"
    repo.mkdir()
    contract = b"---\nname: demo\n---\nbody\n"
    (repo / "SKILL.md").write_bytes(
        contract.replace(b"\n", b"\r\n") + b"appended\r\n"
    )
    manifest_path = _write_manifest(tmp_path / "manifest.json", checker, contract)

    errors, _warnings = checker.verify(repo, manifest_path)

    assert errors == []


def test_substantive_skill_contract_change_is_rejected(tmp_path):
    checker = _load_checker()
    repo = tmp_path / "repo"
    repo.mkdir()
    contract = b"---\nname: demo\n---\nbody\n"
    tampered = contract.replace(b"body", b"copy")
    (repo / "SKILL.md").write_bytes(tampered.replace(b"\n", b"\r\n"))
    manifest_path = _write_manifest(tmp_path / "manifest.json", checker, contract)

    errors, _warnings = checker.verify(repo, manifest_path)

    assert any("reviewed contract changed" in error for error in errors)
