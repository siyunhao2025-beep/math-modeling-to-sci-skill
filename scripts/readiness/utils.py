from __future__ import annotations

from collections import Counter
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}")


def load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | os.PathLike[str], data: Any) -> str:
    common.save_json_atomic(str(path), data)
    return str(path)


def ir_text(ir: dict) -> str:
    parts: list[str] = []
    meta = ir.get("meta", {})
    for key in ("title", "abstract"):
        if meta.get(key):
            parts.append(str(meta[key]))
    for sec in ir.get("sections", []):
        if sec.get("heading"):
            parts.append(str(sec["heading"]))
        for block in sec.get("blocks", []):
            if block.get("text"):
                parts.append(str(block["text"]))
    return "\n".join(parts)


def tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def cosine_similarity(a: str, b: str) -> float:
    ca, cb = Counter(tokens(a)), Counter(tokens(b))
    if not ca or not cb:
        return 0.0
    dot = sum(v * cb.get(k, 0) for k, v in ca.items())
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    return round(dot / (na * nb), 4) if na and nb else 0.0


def normalize_text(text: str) -> str:
    return " ".join(tokens(text))


def title_similarity(a: str, b: str) -> float:
    ta, tb = set(tokens(a)), set(tokens(b))
    if not ta or not tb:
        return 0.0
    return round(len(ta & tb) / len(ta | tb), 4)


def ensure_dir(path: str | os.PathLike[str]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
