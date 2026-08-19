"""ingest.py — S1 输入解析：Word / LaTeX / Markdown → manuscript.ir.json。

这是确定性解析层：不判断学术内容，只把原文结构化为 IR。
语义角色(semantic_role)的*精调*交给提示词，这里只做基于标题关键词的初判。
"""
from __future__ import annotations

import os
import re
import sys

from common import (load_json, repo_path, save_json_atomic, sha256_of,
                    utcnow_iso, validate_against_schema, count_words)
from audit import AuditLogger

IR_SCHEMA = repo_path("config", "schema", "manuscript.schema.json")
PARSER_NAME = "parse_ingest.py@1.0.0"


# --------------------------------------------------------------------------
# 语义角色初判（仅基于标题/关键字，粗粒度）
# --------------------------------------------------------------------------
ROLE_KEYWORDS = [
    ("abstract", ["abstract"]),
    ("introduction", ["introduction", "intro", "引言", "背景"]),
    ("related_work", ["related work", "literature", "相关工作", "文献综述"]),
    ("problem_statement", ["problem", "问题陈述", "问题描述"]),
    ("assumptions", ["assumption", "假设"]),
    ("notation", ["notation", "符号", "nomenclature"]),
    ("methodology", ["method", "methodology", "方法", "建模", "model"]),
    ("model_formulation", ["model formulation", "model", "模型建立", "建模"]),
    ("algorithm", ["algorithm", "算法"]),
    ("experiments", ["experiment", "实验", "数值实验", "numerical"]),
    ("results", ["result", "结果", "仿真"]),
    ("discussion", ["discussion", "讨论"]),
    ("sensitivity_analysis", ["sensitivity", "敏感性", "鲁棒性", "robustness"]),
    ("conclusion", ["conclusion", "结论", "总结"]),
    ("limitations", ["limitation", "不足", "局限"]),
    ("future_work", ["future work", "展望", "未来工作"]),
    ("acknowledgements", ["acknowledg", "致谢"]),
    ("references", ["reference", "参考文献"]),
    ("appendix", ["appendix", "附录"]),
]


def guess_role(heading: str) -> tuple[str, float]:
    h = (heading or "").lower()
    for role, kws in ROLE_KEYWORDS:
        for kw in kws:
            if kw in h:
                return role, 0.75
    return "unclassified", 0.3


EQUATION_INLINE = re.compile(r"\$([^$]+)\$|\\\((.+?)\\\)")
EQUATION_DISPLAY = re.compile(r"\$\$(.+?)\$\$|\\\[(.*?)\\\]", re.S)


# --------------------------------------------------------------------------
# LaTeX / Markdown 解析
# --------------------------------------------------------------------------
def parse_latex(text: str) -> dict:
    lines = text.splitlines()
    sections = []
    equations = []
    figures = []
    tables = []
    eq_idx = fig_idx = tab_idx = 0
    cur = None
    sec_idx = 0
    in_doc = False
    in_abstract = False
    abstract_parts = []
    title = None
    in_eq = False
    eq_buf = []

    # 结构性命令（前导区与文档骨架），不作为正文段落
    SKIP_RE = re.compile(
        r"^\s*\\(documentclass|usepackage|title|author|date|maketitle|"
        r"begin\{document\}|end\{document\}|bibliographystyle|bibliography|"
        r"keywords)\b"
    )

    def flush(sec):
        nonlocal cur
        if cur is not None:
            cur["word_count"] = count_words(" ".join(b.get("text") or "" for b in cur["blocks"]))
            sections.append(cur)
        cur = sec

    def emit(latex):
        """登记一条公式到 equations 列表并追加到当前章节的 block。"""
        nonlocal eq_idx
        eq_idx += 1
        eid = f"eq-{eq_idx}"
        equations.append({"id": eid, "latex": latex, "numbered": True,
                          "environment": "equation", "referenced_in": [cur["id"]] if cur else []})
        if cur is not None:
            cur["blocks"].append({"type": "equation", "ref_id": eid, "latex": latex})

    for line in lines:
        # 提取标题
        tm = re.match(r"^\s*\\title\{([^}]*)\}", line)
        if tm and title is None:
            title = tm.group(1)
        # 进入文档体之前的前导区整体跳过
        if not in_doc:
            if "\\begin{document}" in line:
                in_doc = True
            continue
        if "\\end{document}" in line:
            break
        if re.match(r"\\begin\{abstract\}", line):
            in_abstract = True
            continue
        if re.match(r"\\end\{abstract\}", line):
            in_abstract = False
            continue
        if in_abstract:
            if line.strip():
                abstract_parts.append(line.strip())
            continue
        if SKIP_RE.match(line):
            continue
        # 多行 display 公式块：\[ ... \] 或 \begin{equation} ... \end{equation} 或 $$ ... $$
        s = line.strip()
        if not in_eq:
            if s in (r"\[",) or s.startswith(r"\[") or re.match(r"^\$\$", s) or re.match(r"\\begin\{(equation|equation\*|align|align\*|gather|gather\*)\}", s):
                in_eq = True
                eq_buf = []
                # 单行情况：\[ ... \] 或 $$ ... $$ 同在一行
                closer = None
                if s.startswith(r"\[") and s.endswith(r"\]"):
                    closer = "bracket"
                elif s.startswith("$$") and s.endswith("$$"):
                    closer = "dollar"
                if closer:
                    latex = s[2:-2].strip() if closer == "bracket" else s[2:-2].strip()
                    emit(latex)
                    in_eq = False
                continue
        else:
            if s in (r"\]",) or s.startswith(r"\]") or re.match(r"^\$\$", s):
                latex = " ".join(eq_buf).strip()
                emit(latex)
                in_eq = False
                continue
            if re.match(r"\\end\{(equation|equation\*|align|align\*|gather|gather\*)\}", s):
                latex = " ".join(eq_buf).strip()
                emit(latex)
                in_eq = False
                continue
            eq_buf.append(line.strip())
            continue
        # 章节
        m = re.match(r"\\(section|subsection|subsubsection)\*?\{([^}]*)\}", line)
        if m:
            sec_idx += 1
            role, conf = guess_role(m.group(2))
            flush({"id": f"sec-{sec_idx}", "level": {"section": 1, "subsection": 2, "subsubsection": 3}[m.group(1)],
                   "heading": m.group(2), "semantic_role": role, "role_confidence": conf, "blocks": []})
            continue
        if cur is None and line.strip():
            sec_idx += 1
            flush({"id": f"sec-{sec_idx}", "level": 1, "heading": "(untitled)",
                   "semantic_role": "unclassified", "role_confidence": 0.3, "blocks": []})
        # 图
        fm = re.search(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", line)
        if fm:
            fig_idx += 1
            cap = re.search(r"\\caption\{([^}]*)\}", line)
            figures.append({"id": f"fig-{fig_idx}",
                            "caption": cap.group(1) if cap else f"Figure {fig_idx}",
                            "path": fm.group(2), "referenced_in": [cur["id"]]})
            cur["blocks"].append({"type": "figure", "ref_id": f"fig-{fig_idx}"})
            continue
        # 行内/单行 display 公式
        for dm in EQUATION_DISPLAY.findall(line):
            latex = (dm[0] or dm[1]).strip()
            if not latex:
                continue
            emit(latex)
        # 段落（含行内公式）
        if line.strip():
            cur["blocks"].append({"type": "paragraph", "text": line.strip()})
    flush(None)
    return {"sections": sections, "equations": equations, "figures": figures,
            "tables": tables, "title": title,
            "abstract": "\n".join(abstract_parts) or None}


def parse_markdown(text: str) -> dict:
    sections = []
    equations = []
    figures = []
    tables = []
    eq_idx = fig_idx = tab_idx = 0
    cur = None
    sec_idx = 0
    title = None

    def flush(sec):
        nonlocal cur
        if cur is not None:
            cur["word_count"] = count_words(" ".join(b.get("text") or "" for b in cur["blocks"]))
            sections.append(cur)
        cur = sec

    for line in text.splitlines():
        m = re.match(r"(#{1,5})\s+(.*)", line)
        if m:
            htext = m.group(2).strip()
            # 首个 H1 作为稿件标题，不入章节
            if len(m.group(1)) == 1 and title is None:
                title = htext
                continue
            sec_idx += 1
            role, conf = guess_role(htext)
            flush({"id": f"sec-{sec_idx}", "level": len(m.group(1)), "heading": htext,
                   "semantic_role": role, "role_confidence": conf, "blocks": []})
            continue
        if cur is None and line.strip():
            sec_idx += 1
            flush({"id": f"sec-{sec_idx}", "level": 1, "heading": "(untitled)",
                   "semantic_role": "unclassified", "role_confidence": 0.3, "blocks": []})
        if line.strip().startswith("![") and "](" in line:
            fig_idx += 1
            cap = re.search(r"!\[(.*?)\]\(([^)]*)\)", line)
            figures.append({"id": f"fig-{fig_idx}", "caption": cap.group(1) if cap else f"Figure {fig_idx}",
                            "path": cap.group(2) if cap else None, "referenced_in": [cur["id"]]})
            cur["blocks"].append({"type": "figure", "ref_id": f"fig-{fig_idx}"})
        elif line.strip():
            for dm in EQUATION_DISPLAY.findall(line):
                eq_idx += 1
                latex = (dm[0] or dm[1]).strip()
                equations.append({"id": f"eq-{eq_idx}", "latex": latex, "numbered": True,
                                  "environment": "equation", "referenced_in": [cur["id"]]})
                cur["blocks"].append({"type": "equation", "ref_id": f"eq-{eq_idx}", "latex": latex})
            cur["blocks"].append({"type": "paragraph", "text": line.strip()})
    flush(None)
    return {"sections": sections, "equations": equations, "figures": figures,
            "tables": tables, "title": title, "abstract": None}


# --------------------------------------------------------------------------
# DOCX 解析（python-docx）
# --------------------------------------------------------------------------
def parse_docx(path: str) -> dict:
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx 未安装，无法解析 .docx 输入（硬依赖）")

    doc = Document(path)
    sections = []
    equations = []
    figures = []
    tables = []
    eq_idx = fig_idx = tab_idx = 0
    sec_idx = 0
    cur = None

    def flush(sec):
        nonlocal cur
        if cur is not None:
            cur["word_count"] = count_words(" ".join(b.get("text") or "" for b in cur["blocks"]))
            sections.append(cur)
        cur = sec

    def ensure_sec():
        nonlocal cur, sec_idx
        if cur is None:
            sec_idx += 1
            flush({"id": f"sec-{sec_idx}", "level": 1, "heading": "(untitled)",
                   "semantic_role": "unclassified", "role_confidence": 0.3, "blocks": []})

    # 表格
    for t in doc.tables:
        tab_idx += 1
        header = [c.text.strip() for c in t.rows[0].cells] if t.rows else []
        rows = [[c.text.strip() for c in r.cells] for r in t.rows[1:]]
        tables.append({"id": f"tab-{tab_idx}", "caption": f"Table {tab_idx}",
                       "header": header, "rows": rows, "referenced_in": []})

    for p in doc.paragraphs:
        style = (p.style.name or "").lower() if p.style else ""
        text = p.text.strip()
        if style.startswith("heading") or style.startswith("title"):
            try:
                lvl = int(re.search(r"(\d)", style).group(1)) if re.search(r"(\d)", style) else 1
            except Exception:
                lvl = 1
            sec_idx += 1
            role, conf = guess_role(text)
            flush({"id": f"sec-{sec_idx}", "level": lvl, "heading": text,
                   "semantic_role": role, "role_confidence": conf, "blocks": []})
            continue
        if not text:
            continue
        ensure_sec()
        # 公式（行内 $...$ 或 \(...\)）
        has_eq = False
        for dm in EQUATION_DISPLAY.findall(text):
            eq_idx += 1
            latex = (dm[0] or dm[1]).strip()
            equations.append({"id": f"eq-{eq_idx}", "latex": latex, "numbered": True,
                              "environment": "equation", "referenced_in": [cur["id"]]})
            cur["blocks"].append({"type": "equation", "ref_id": f"eq-{eq_idx}", "latex": latex})
            has_eq = True
        if not has_eq:
            cur["blocks"].append({"type": "paragraph", "text": text})
        # 行内图片（docx 中图片以 run 内的 drawing 表示，python-docx 不直接暴露；此处计数占位）
    flush(None)
    return {"sections": sections, "equations": equations, "figures": figures, "tables": tables}


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def build_ir(source_file: str, source_format: str, source_text: str = None) -> dict:
    ext = os.path.splitext(source_file)[1].lower()
    if source_format == "docx" or ext == ".docx":
        parsed = parse_docx(source_file)
    elif source_format in ("latex", "latex-project") or ext in (".tex",):
        parsed = parse_latex(source_text or open(source_file, encoding="utf-8").read())
    elif ext in (".md", ".markdown") or source_format == "markdown":
        parsed = parse_markdown(source_text or open(source_file, encoding="utf-8").read())
    else:
        raise ValueError(f"不支持的输入格式: {ext or source_format}")

    ir = {
        "schema_version": "1.0",
        "provenance": {
            "source_file": os.path.basename(source_file),
            "source_format": source_format if source_format != "latex-project" else "latex-project",
            "source_sha256": sha256_of(source_file) if os.path.isfile(source_file) else None,
            "parsed_at": utcnow_iso(),
            "parser": PARSER_NAME,
            "stage": "S1",
        },
        "meta": {
            "title": parsed.get("title") or "(未命名稿件)",
            "language": detect_language(source_text or ""),
            "target_language": "en",
            "authors": [],
            "abstract": parsed.get("abstract"),
            "keywords": [],
        },
        "sections": parsed["sections"],
        "equations": parsed["equations"],
        "figures": parsed["figures"],
        "tables": parsed["tables"],
        "references": [],
        "symbol_map": {},
        "gaps": [],
        "rewrite_log": [],
    }
    return ir


def detect_language(text: str) -> str:
    from common import find_cjk
    if not text:
        return "en"
    cjk = len(find_cjk(text))
    total = max(1, len(re.findall(r"\w+", text)))
    if cjk / total > 0.2:
        return "zh"
    return "en"


def run(input_path: str, workdir: str, source_format: str = None) -> str:
    logger = AuditLogger(workdir)
    ext = os.path.splitext(input_path)[1].lower()
    if source_format is None:
        source_format = {".docx": "docx", ".tex": "latex", ".md": "markdown",
                         ".markdown": "markdown"}.get(ext, "markdown")
    logger.log("stage_start", "S1", artifacts=[{"path": input_path}])
    ir = build_ir(input_path, source_format)
    out = os.path.join(workdir, "01-parse", "manuscript.ir.json")
    save_json_atomic(out, ir)
    errs = validate_against_schema(ir, IR_SCHEMA)
    if errs:
        logger.log("gate_decision", "S1", gate="G1", result="fail",
                   gate_metrics={"schema_errors": errs})
        raise SystemExit(f"IR 校验失败:\n" + "\n".join(errs))
    logger.log("stage_end", "S1", artifacts=[{"path": out}],
               gate_metrics={"sections": len(ir["sections"]),
                             "equations": len(ir["equations"])})
    return out


if __name__ == "__main__":
    inp = sys.argv[1]
    wd = sys.argv[2] if len(sys.argv) > 2 else "runs/demo"
    fmt = sys.argv[3] if len(sys.argv) > 3 else None
    print(run(inp, wd, fmt))
