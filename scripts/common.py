"""common.py — 共享工具：路径、IO、schema 校验、原子写入、sha256。

所有阶段脚本都从这里导入公共能力，保证行为一致。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Optional

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(REPO_ROOT, "config", "schema")
CONFIG_DIR = os.path.join(REPO_ROOT, "config")


# --------------------------------------------------------------------------
# 路径与 IO
# --------------------------------------------------------------------------
def repo_path(*parts: str) -> str:
    return os.path.join(REPO_ROOT, *parts)


def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_atomic(path: str, data: Any, indent: int = 2) -> None:
    """原子写入：先写 .tmp 再替换，避免半截文件污染下游。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    os.replace(tmp, path)


def sha256_of(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Schema 校验
# --------------------------------------------------------------------------
def validate_against_schema(data: Any, schema_path: str) -> list[str]:
    """用 draft-07 校验，返回错误字符串列表（空=通过）。"""
    import jsonschema  # 局部导入，避免无依赖时启动即崩

    schema = load_json(schema_path)
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for err in validator.iter_errors(data):
        loc = " / ".join(str(p) for p in err.path) or "<root>"
        errors.append(f"[{loc}] {err.message}")
    return errors


# --------------------------------------------------------------------------
# 文本启发式工具
# --------------------------------------------------------------------------
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")
PLACEHOLDER_RES = [
    (r"\[\[MISSING", "[[MISSING]]"),
    (r"\[\[UNVERIFIED_REF", "[[UNVERIFIED_REF]]"),
    (r"\bTODO\b", "TODO"),
    (r"\bTBD\b", "TBD"),
    (r"\bXXX\b", "XXX"),
    (r"\\ref\{\?\?\}", r"\ref{??}"),
    (r"\?\?", "??"),
]


def find_cjk(text: str) -> list[str]:
    return CJK_RE.findall(text or "")


def find_placeholders(text: str) -> list[str]:
    found = []
    for pat, label in PLACEHOLDER_RES:
        if re.search(pat, text or ""):
            found.append(label)
    return found


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def utcnow_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
