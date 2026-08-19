#!/usr/bin/env python3
"""Compatibility CLI for a real LaTeX compile check when toolchain is available."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _compat import dump_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main_tex = os.path.join(args.build, "main.tex")
    if not os.path.isfile(main_tex):
        dump_json(args.out, {"checker": "latex_compile_check", "status": "fail", "detail": "main.tex missing"})
        return 2
    latexmk = shutil.which("latexmk")
    pdflatex = shutil.which("pdflatex")
    if not (latexmk or pdflatex):
        dump_json(args.out, {
            "checker": "latex_compile_check",
            "status": "skipped",
            "detail": "latexmk/pdflatex unavailable; G6 must record an explicit degrade",
        })
        return 0
    cmd = (
        [latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
        if latexmk else
        [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    )
    proc = subprocess.run(cmd, cwd=args.build, capture_output=True, text=True, timeout=120)
    result = {
        "checker": "latex_compile_check",
        "status": "pass" if proc.returncode == 0 else "fail",
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
        "stdout_tail": proc.stdout[-2000:],
    }
    dump_json(args.out, result)
    return 0 if proc.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
