"""Shared implementation for documented validation compatibility CLIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import common
from _compat import dump_json, load_flat_module


def workdir_from_build(build: str) -> str:
    p = Path(build).resolve()
    if p.name == "build" and p.parent.name == "05-template":
        return str(p.parent.parent)
    if "05-template" in p.parts:
        idx = p.parts.index("05-template")
        return str(Path(*p.parts[:idx]))
    raise RuntimeError(
        "--build must point to <workdir>/05-template/build so the rewritten IR can be located"
    )


def manuscript_for_build(build: str) -> tuple[str, dict]:
    wd = workdir_from_build(build)
    path = os.path.join(wd, "02-rewrite", "manuscript.rewritten.json")
    if not os.path.isfile(path):
        raise RuntimeError(f"rewritten IR missing: {path}")
    return wd, common.load_json(path)


def write_checker_result(name: str, status: str, findings, skip, out: str) -> int:
    data = {
        "checker": name,
        "status": status,
        "skip_reason": skip,
        "findings": [f.to_dict() if hasattr(f, "to_dict") else f for f in findings],
    }
    dump_json(out, data)
    return 2 if any((f.to_dict() if hasattr(f, "to_dict") else f).get("severity") == "error" for f in findings) else 0


def bib_keys(build: str) -> set[str]:
    bib = os.path.join(build, "references.bib")
    if not os.path.isfile(bib) or os.path.getsize(bib) == 0:
        return set()
    import bibtexparser
    with open(bib, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return {e.get("ID") for e in db.entries if e.get("ID")}


def validation_module():
    return load_flat_module("validate")
