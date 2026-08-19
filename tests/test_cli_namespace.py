from __future__ import annotations

import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def test_canonical_flat_modules_win_import_resolution():
    sys.path.insert(0, str(SCRIPTS))
    try:
        for name in ("ingest", "journals", "render", "validate"):
            sys.modules.pop(name, None)
            module = importlib.import_module(name)
            assert Path(module.__file__).resolve() == (SCRIPTS / f"{name}.py").resolve()
    finally:
        try:
            sys.path.remove(str(SCRIPTS))
        except ValueError:
            pass


def test_compatibility_cli_directories_are_not_packages():
    for name in ("ingest", "journals", "render", "validate"):
        shim = SCRIPTS / name
        assert shim.is_dir()
        assert not (shim / "__init__.py").exists(), f"{shim} must remain package-less"
        assert (SCRIPTS / f"{name}.py").is_file()


def test_shims_delegate_instead_of_becoming_parallel_implementations():
    samples = [
        SCRIPTS / "ingest" / "parse_latex.py",
        SCRIPTS / "journals" / "match_journals.py",
        SCRIPTS / "validate" / "check_citations.py",
    ]
    for path in samples:
        body = path.read_text(encoding="utf-8")
        assert "_compat" in body or "_validation_cli" in body or "load_flat_module" in body
