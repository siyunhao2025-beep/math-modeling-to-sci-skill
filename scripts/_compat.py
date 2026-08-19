"""Helpers for compatibility command wrappers documented by the Skill."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent


def load_flat_module(name: str):
    """Load scripts/<name>.py even when scripts/<name>/ wrappers also exist."""
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_flat_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load flat module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def workdir_from_output(output: str, stage_dir: str) -> str:
    """Infer run workdir from an output path containing a stage directory."""
    p = Path(output).resolve()
    parts = list(p.parts)
    if stage_dir in parts:
        idx = parts.index(stage_dir)
        return str(Path(*parts[:idx])) if idx > 0 else str(Path("."))
    return str(p.parent)


def copy_if_needed(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copy2(src, dst)


def dump_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
