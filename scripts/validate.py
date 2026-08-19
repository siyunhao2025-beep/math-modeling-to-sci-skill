"""validate.py — S6 多轮校验。对成稿 IR 运行各检查器，产出 validation-roundN.json。

检查器（对应 validation.schema.json 的 checkers.name）：
  validate_ir / check_citations / check_figures_tables / check_equations /
  check_language / check_cjk_residue / check_journal_constraints / cross_validate
"""
from __future__ import annotations

import os
import re
import sys

from common import (load_json, repo_path, save_json_atomic, utcnow_iso,
                    validate_against_schema, find_cjk, find_placeholders, count_words)
from audit import AuditLogger

VALIDATION_SCHEMA = repo_path("config", "schema", "validation.schema.json")


class Finding:
    def __init__(self, fid, severity, message, location="", suggestion="", auto_fixable=False):
        self.fid = fid
        self.severity = severity
        self.message = message
        self.location = location
        self.suggestion = suggestion
        self.auto_fixable = auto_fixable

    def to_dict(self):
        return {
            "id": self.fid,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
        }


def _all_text(manuscript: dict) -> str:
    parts = []
    for sec in manuscript.get("sections", []):
        for b in sec.get("blocks", []):
            if b.get("text"):
                parts.append(b["text"])
            if b.get("latex"):
                parts.append(b["latex"])
    parts.append(manuscript.get("meta", {}).get("abstract") or "")
    return "\n".join(parts)


def checker_validate_ir(ms: dict):
    errs = validate_against_schema(ms, repo_path("config", "schema", "manuscript.schema.json"))
    findings = [Finding(f"ir-{i}", "error", e) for i, e in enumerate(errs)] if errs else []
    status = "fail" if errs else "pass"
    return status, findings, None


def checker_cjk(ms: dict, target_lang="en"):
    if target_lang != "en":
        return "skipped", [], "target language is not en"
    hits = find_cjk(_all_text(ms))
    findings = []
    if hits:
        findings.append(Finding("cjk-1", "error",
                                 f"目标语言为 en 但成稿残留 {len(hits)} 个 CJK 字符",
                                 suggestion="翻译或删除 CJK 文本", auto_fixable=False))
    return ("fail" if findings else "pass"), findings, None


def checker_placeholders(ms: dict):
    findings = []
    text = _all_text(ms)
    ph = find_placeholders(text)
    if ph:
        findings.append(Finding("ph-1", "error",
                                 f"成稿含禁止占位符: {', '.join(ph)}",
                                 suggestion="删除该断言并保留在 gaps 清单交作者补", auto_fixable=False))
    return ("fail" if findings else "pass"), findings, None


def checker_citations(ms: dict, bib_keys: set):
    findings = []
    cited = set()
    for sec in ms.get("sections", []):
        for b in sec.get("blocks", []):
            for c in b.get("citations", []):
                cited.add(c)
            for m in re.findall(r"\\cite\{([^}]*)\}", b.get("text", "") or ""):
                cited.update(k.strip() for k in m.split(","))
    for c in cited:
        if bib_keys and c not in bib_keys:
            findings.append(Finding(f"cite-{c}", "error",
                                     f"正文引用 \\cite{{{c}}} 不在 references 中",
                                     location=c, suggestion="补充 bib 条目或删除引用", auto_fixable=False))
    if bib_keys:
        for k in bib_keys:
            if k not in cited:
                findings.append(Finding(f"bib-{k}", "warning",
                                         f"references 中有未引用的条目 {k}",
                                         location=k, auto_fixable=True))
    status = "fail" if any(f.severity == "error" for f in findings) else "pass"
    return status, findings, None


def checker_figures_tables(ms: dict):
    findings = []
    for fig in ms.get("figures", []):
        if fig.get("referenced_in") is None or len(fig.get("referenced_in", [])) == 0:
            findings.append(Finding(f"fig-{fig['id']}", "warning",
                                     f"图 {fig['id']} 未被正文引用（孤儿图）",
                                     location=fig["id"], auto_fixable=True))
    for tab in ms.get("tables", []):
        if tab.get("referenced_in") is None or len(tab.get("referenced_in", [])) == 0:
            findings.append(Finding(f"tab-{tab['id']}", "warning",
                                     f"表 {tab['id']} 未被正文引用（孤儿表）",
                                     location=tab["id"], auto_fixable=True))
    status = "fail" if any(f.severity == "error" for f in findings) else "pass"
    return status, findings, None


def checker_equations(ms: dict):
    findings = []
    for eq in ms.get("equations", []):
        if not eq.get("referenced_in"):
            findings.append(Finding(f"eq-{eq['id']}", "warning",
                                     f"公式 {eq['id']} 未被引用", location=eq["id"], auto_fixable=True))
    return ("pass" if not findings else "pass"), findings, None


def checker_journal_constraints(ms: dict, constraints: dict):
    findings = []
    if not constraints:
        return "skipped", [], "no constraints supplied"
    meta = ms.get("meta", {})
    wc = meta.get("word_count") or count_words(_all_text(ms))
    if constraints.get("max_words") and wc > constraints["max_words"]:
        findings.append(Finding("jc-words", "error",
                                 f"字数 {wc} 超过上限 {constraints['max_words']}",
                                 suggestion="压缩正文或摘要", auto_fixable=False))
    kw = meta.get("keywords", [])
    if constraints.get("max_keywords") and len(kw) > constraints["max_keywords"]:
        findings.append(Finding("jc-kw", "warning",
                                 f"关键词 {len(kw)} 超过上限 {constraints['max_keywords']}",
                                 auto_fixable=True))
    status = "fail" if any(f.severity == "error" for f in findings) else "pass"
    return status, findings, None


def run(manuscript_path: str, workdir: str, bib_path: str = None,
        constraints: dict = None, round_no: int = 1, target_journal: str = None) -> str:
    logger = AuditLogger(workdir)
    ms = load_json(manuscript_path)
    bib_keys = set()
    if bib_path and os.path.isfile(bib_path):
        import bibtexparser
        with open(bib_path, encoding="utf-8") as f:
            db = bibtexparser.load(f)
        bib_keys = {e.get("ID") for e in db.entries}

    target_lang = ms.get("meta", {}).get("target_language", "en")
    checkers = []
    all_findings = []

    def add(name, status, findings, skip=None):
        checkers.append({"name": name, "status": status,
                         "skip_reason": skip, "findings": [f.to_dict() for f in findings]})
        all_findings.extend(findings)

    s, f, sk = checker_validate_ir(ms); add("validate_ir", s, f, sk)
    s, f, sk = checker_cjk(ms, target_lang); add("check_cjk_residue", s, f, sk)
    s, f, sk = checker_placeholders(ms); add("check_language", s, f, None)
    s, f, sk = checker_citations(ms, bib_keys); add("check_citations", s, f, None)
    s, f, sk = checker_figures_tables(ms); add("check_figures_tables", s, f, None)
    s, f, sk = checker_equations(ms); add("check_equations", s, f, None)
    s, f, sk = checker_journal_constraints(ms, constraints or {}); add("check_journal_constraints", s, f, sk)

    err = sum(1 for f in all_findings if f.severity == "error")
    warn = sum(1 for f in all_findings if f.severity == "warning")
    auto = sum(1 for f in all_findings if f.auto_fixable)
    verdict = "PASS" if err == 0 else ("PASS_WITH_WARNINGS" if err == 0 else "FAIL_RETRY")

    result = {
        "schema_version": "1.0",
        "round": round_no,
        "validated_at": utcnow_iso(),
        "target_build": "05-template/build",
        "target_journal": target_journal,
        "checkers": checkers,
        "summary": {
            "error_count": err,
            "warning_count": warn,
            "info_count": 0,
            "auto_fixed_count": 0,
            "unresolved_error_ids": [f.fid for f in all_findings if f.severity == "error"],
            "checkers_skipped": [c["name"] for c in checkers if c["status"] == "skipped"],
        },
        "verdict": verdict,
        "next_action": "proceed_to_s7" if err == 0 else "retry_round",
    }
    out = os.path.join(workdir, "06-validate", f"validation-round{round_no}.json")
    save_json_atomic(out, result)
    # 同时写 final（多轮时由编排器覆盖）
    final = os.path.join(workdir, "06-validate", "validation-final.json")
    save_json_atomic(final, result)
    logger.log("gate_decision", "S6", gate="G6",
               gate_metrics={"error_count": err, "warning_count": warn, "round": round_no},
               action="proceed" if err == 0 else "retry")
    return out


if __name__ == "__main__":
    mp = sys.argv[1]
    wd = sys.argv[2] if len(sys.argv) > 2 else "runs/demo"
    bp = sys.argv[3] if len(sys.argv) > 3 else None
    print(run(mp, wd, bp))
