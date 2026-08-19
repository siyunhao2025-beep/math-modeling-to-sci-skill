"""Parse a zipped LaTeX project into the same manuscript IR used by S1."""
from __future__ import annotations

import os
from pathlib import PurePosixPath
import re
import tempfile
import zipfile

import common
from audit import AuditLogger
from _compat import load_flat_module


def _safe_tex_members(zf: zipfile.ZipFile) -> list[str]:
    members = []
    for name in zf.namelist():
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts:
            continue
        if name.lower().endswith(".tex") and not name.endswith("/"):
            members.append(name)
    return members


def _choose_main(zf: zipfile.ZipFile, tex_members: list[str]) -> str:
    candidates = []
    for name in tex_members:
        try:
            text = zf.read(name).decode("utf-8")
        except UnicodeDecodeError:
            text = zf.read(name).decode("utf-8", errors="replace")
        score = 0
        if re.search(r"\\documentclass(?:\[[^\]]*\])?\{", text):
            score += 10
        if r"\begin{document}" in text:
            score += 5
        if PurePosixPath(name).name.lower() in ("main.tex", "manuscript.tex", "paper.tex"):
            score += 3
        candidates.append((score, -len(PurePosixPath(name).parts), name))
    candidates.sort(reverse=True)
    if not candidates or candidates[0][0] <= 0:
        raise RuntimeError("No main LaTeX file with \\documentclass / \\begin{document} was found in ZIP")
    return candidates[0][2]


def _resolve_project_text(zf: zipfile.ZipFile, main_name: str) -> str:
    """Resolve local \input/\include recursively for parsing; keep source commands as comments."""
    seen: set[str] = set()

    def read(name: str) -> str:
        norm = str(PurePosixPath(name))
        if norm in seen:
            return f"\n% [cycle skipped: {norm}]\n"
        seen.add(norm)
        raw = zf.read(norm)
        text = raw.decode("utf-8", errors="replace")
        base = PurePosixPath(norm).parent

        def repl(match: re.Match) -> str:
            ref = match.group(1).strip()
            if not ref.lower().endswith(".tex"):
                ref += ".tex"
            target = str(base / ref)
            if target not in zf.namelist():
                return match.group(0) + f" % [missing include: {target}]"
            return f"\n% BEGIN included {target}\n{read(target)}\n% END included {target}\n"

        return re.sub(r"\\(?:input|include)\{([^}]+)\}", repl, text)

    return read(main_name)


def run(input_zip: str, workdir: str) -> str:
    logger = AuditLogger(workdir)
    logger.log("stage_start", "S1", artifacts=[{"path": input_zip}], detail="latex-project ZIP")
    if not zipfile.is_zipfile(input_zip):
        raise RuntimeError(f"not a valid ZIP file: {input_zip}")
    with zipfile.ZipFile(input_zip) as zf:
        members = _safe_tex_members(zf)
        if not members:
            raise RuntimeError("ZIP contains no safe .tex files")
        main_name = _choose_main(zf, members)
        source_text = _resolve_project_text(zf, main_name)

    ingest = load_flat_module("ingest")
    ir = ingest.build_ir(input_zip, "latex-project", source_text=source_text)
    ir["provenance"]["parser"] = "latex-project-zip@1.1.0"
    ir.setdefault("gaps", [])
    # record main member without adding non-schema provenance fields
    ir["rewrite_log"] = ir.get("rewrite_log", [])

    out = os.path.join(workdir, "01-parse", "manuscript.ir.json")
    common.save_json_atomic(out, ir)
    errors = common.validate_against_schema(
        ir, common.repo_path("config", "schema", "manuscript.schema.json")
    )
    if errors:
        logger.log("gate_decision", "S1", gate="G1", result="fail", gate_metrics={"schema_errors": errors})
        raise RuntimeError("IR schema validation failed:\n" + "\n".join(errors))
    logger.log(
        "stage_end",
        "S1",
        artifacts=[{"path": out}],
        gate_metrics={"sections": len(ir.get("sections", [])), "equations": len(ir.get("equations", [])), "zip_main": main_name},
    )
    return out
