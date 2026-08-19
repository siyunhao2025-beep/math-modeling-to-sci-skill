"""render.py — S5 模板适配。把定稿 IR 重组为可编译 LaTeX 骨架。

模板级别（对应 G5 降级链）：
  level 1 官方 cls  → 使用 journal.template.latex 指定的文档类（此处退化为出版商通用类）
  level 2/3 出版商/内置 → 按 publisher 选 elsarticle / IEEEtran / sn-jnl / article
  level 4 标准 article → \\documentclass{article}

本脚本不下载网络模板，统一产出"可编译骨架"，由提示词/S6 处理保真度与官方替换。
"""
from __future__ import annotations

import os
import sys

from common import (load_json, load_yaml, repo_path, save_json_atomic, utcnow_iso)
from audit import AuditLogger

PUB_DOCCLASS = {
    "Elsevier": "elsarticle",
    "IEEE": "IEEEtran",
    "Springer": "sn-jnl",
}


def render_section(sec: dict, section_map: list) -> str:
    lines = [f"\\section{{{sec['heading']}}}"]
    sid = sec["id"]
    for b in sec.get("blocks", []):
        if b.get("type") == "paragraph":
            lines.append(b.get("text", ""))
        elif b.get("type") == "equation":
            latex = b.get("latex") or ""
            lines.append(f"\\begin{{equation}}\n{latex}\n\\end{{equation}}")
        elif b.get("type") == "figure":
            ref = b.get("ref_id")
            lines.append(f"% 图 {ref} 见 figures 区")
        elif b.get("type") == "table":
            ref = b.get("ref_id")
            lines.append(f"% 表 {ref} 见 tables 区")
        elif b.get("type") == "list":
            items = b.get("items", []) or []
            env = "enumerate" if b.get("ordered") else "itemize"
            lines.append(f"\\begin{{{env}}}")
            for it in items:
                lines.append(f"  \\item {it}")
            lines.append(f"\\end{{{env}}}")
    section_map.append({"ir_id": sid, "semantic_role": sec.get("semantic_role"),
                       "placed": True, "heading": sec["heading"]})
    return "\n".join(lines)


def render_figures(figures: list) -> str:
    out = []
    for f in figures:
        out.append("\\begin{figure}[htbp]")
        out.append(f"  \\centering")
        out.append(f"  % 图源: {f.get('path') or 'MISSING'}")
        out.append(f"  \\caption{{{f.get('caption', f['id'])}}}")
        out.append(f"  \\label{{fig:{f['id']}}}")
        out.append("\\end{figure}")
    return "\n".join(out)


def render_tables(tables: list) -> str:
    out = []
    for t in tables:
        out.append("\\begin{table}[htbp]")
        out.append("  \\centering")
        header = t.get("header", [])
        cols = "l" * max(1, len(header))
        out.append(f"  \\begin{{tabular}}{{{cols}}}")
        out.append("    \\toprule")
        if header:
            out.append("    " + " & ".join(header) + " \\\\")
            out.append("    \\midrule")
        for row in t.get("rows", []):
            out.append("    " + " & ".join(row) + " \\\\")
        out.append("    \\bottomrule")
        out.append("  \\end{tabular}")
        out.append(f"  \\caption{{{t.get('caption', t['id'])}}}")
        out.append(f"  \\label{{tab:{t['id']}}}")
        out.append("\\end{table}")
    return "\n".join(out)


def render_bib(references: list) -> str:
    entries = []
    for r in references:
        if r.get("origin") == "added_by_s2" and not str(r.get("verification", {}).get("status", "")).startswith("verified"):
            continue  # 未验证引用不进 bib
        fields = [f"  title = {{{r.get('title','')}}}"]
        if r.get("authors"):
            fields.append(f"  author = {{{' and '.join(r['authors'])}}}")
        if r.get("year"):
            fields.append(f"  year = {{{r['year']}}}")
        if r.get("venue"):
            fields.append(f"  journal = {{{r['venue']}}}")
        if r.get("doi"):
            fields.append(f"  doi = {{{r['doi']}}}")
        if r.get("url"):
            fields.append(f"  url = {{{r['url']}}}")
        entry = f"@{r.get('entry_type','article')}{{{r.get('key','unknown')},\n" + ",\n".join(fields) + "\n}"
        entries.append(entry)
    return "\n\n".join(entries)


def run(manuscript_path: str, workdir: str, journal_match_path: str = None) -> str:
    logger = AuditLogger(workdir)
    ms = load_json(manuscript_path)

    # 确定模板级别
    docclass = "article"
    template_level = 4
    template_source = "standard article class"
    constraints = {}
    if journal_match_path and os.path.isfile(journal_match_path):
        jm = load_json(journal_match_path)
        rec0 = (jm.get("recommendations") or [{}])[0]
        pub = rec0.get("publisher")
        constraints = rec0.get("constraints") or {}
        if pub in PUB_DOCCLASS:
            docclass = PUB_DOCCLASS[pub]
            template_level = 2
            template_source = f"publisher-generic ({pub})"
        tf = rec0.get("template") or {}
        if tf.get("bundled_fallback"):
            template_source += f"; fallback={tf['bundled_fallback']}"

    meta = ms.get("meta", {})
    title = meta.get("title", "Untitled Manuscript")
    abstract = meta.get("abstract") or "Abstract missing — to be supplied by author."
    keywords = meta.get("keywords", [])

    # 保留源文档的章节顺序（真实学术化重组由 S2 提示词负责）
    secs = ms.get("sections", [])

    section_map = []
    body = "\n\n".join(render_section(s, section_map) for s in secs)

    bibstyle = (constraints.get("reference_style") or "plain").split()[0]
    if "IEEE" in docclass:
        bibstyle = "IEEEtran"
    elif docclass == "elsarticle":
        bibstyle = "elsarticle-num"

    tex = f"""\\documentclass[11pt]{{{docclass}}}

\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath,amssymb,graphicx,booktabs}}
\\title{{{title}}}

\\begin{{document}}
\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

\\keywords{{{', '.join(keywords)}}}

{body}

{render_figures(ms.get('figures', []))}

{render_tables(ms.get('tables', []))}

\\bibliographystyle{{{bibstyle}}}
\\bibliography{{references}}

\\end{{document}}
"""
    build = os.path.join(workdir, "05-template", "build")
    os.makedirs(build, exist_ok=True)
    main_path = os.path.join(build, "main.tex")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(tex)

    bib_path = os.path.join(build, "references.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(render_bib(ms.get("references", [])))

    manifest = {
        "schema_version": "1.0",
        "generated_at": utcnow_iso(),
        "template_level": template_level,
        "template_source": template_source,
        "document_class": docclass,
        "bib_style": bibstyle,
        "section_map": section_map,
        "constraints_snapshot": constraints,
        "is_official_template": False,
    }
    save_json_atomic(os.path.join(workdir, "05-template", "MANIFEST.json"), manifest)

    unmapped = {"unmapped_sections": [], "note": "所有 IR section 均已放置（S5-03）。"}
    save_json_atomic(os.path.join(workdir, "05-template", "unmapped.json"), unmapped)

    logger.log("stage_end", "S5", artifacts=[{"path": main_path}, {"path": bib_path}],
               gate_metrics={"template_level": template_level, "sections_placed": len(section_map)})
    return main_path


if __name__ == "__main__":
    mp = sys.argv[1]
    wd = sys.argv[2] if len(sys.argv) > 2 else "runs/demo"
    jm = sys.argv[3] if len(sys.argv) > 3 else None
    print(run(mp, wd, jm))
