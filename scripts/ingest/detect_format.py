#!/usr/bin/env python3
"""Compatibility CLI: detect manuscript input format."""
from __future__ import annotations

import argparse
import os
import zipfile


def detect(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return "docx"
    if ext == ".tex":
        return "latex"
    if ext in (".md", ".markdown"):
        return "markdown"
    if ext == ".zip":
        try:
            with zipfile.ZipFile(path) as zf:
                names = [n.lower() for n in zf.namelist()]
                if any(n.endswith(".tex") for n in names):
                    return "latex-project"
        except zipfile.BadZipFile:
            pass
    return "unknown"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()
    if not os.path.isfile(args.input):
        ap.error(f"input file does not exist: {args.input}")
    print(detect(args.input))
