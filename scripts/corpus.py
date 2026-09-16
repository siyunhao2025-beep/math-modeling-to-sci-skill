#!/usr/bin/env python3
"""Repository-root CLI bridge to the isolated Research Mother package."""
from pathlib import Path
import runpy
import sys

if __name__ == "__main__":
    directory = Path(__file__).resolve().parents[1] / "research-mother" / "scripts"
    sys.path.insert(0, str(directory))
    runpy.run_path(str(directory / "corpus.py"), run_name="__main__")
