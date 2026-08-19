"""run_pipeline.py — 编排入口。串联 S1→S7 的确定性步骤。

说明：
- S2（学术化改写）与 S3（质量评估）本质是 AI 推理任务，由 Skill 提示词驱动。
- 本 CLI 在 `--ai-stub`（默认开）下用"直通 + 占位评估"让端到端流程可跑通 demo；
  生产环境应关闭 --ai-stub，由编排器加载 02/03 提示词执行真实改写与评估。
- `--probe-env` 用于 S0 探测环境能力矩阵（对应编排器启动前检查）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import common
from audit import AuditLogger
import ingest, journals, render, validate, report

STAGES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]


def probe_env() -> dict:
    def has(mod):
        try:
            __import__(mod)
            return True
        except Exception:
            return False

    def has_bin(name):
        return shutil.which(name) is not None

    net = False
    try:
        subprocess.run([sys.executable, "-c", "import urllib.request,socket;socket.setdefaulttimeout(3);"
                        "urllib.request.urlopen('https://api.crossref.org')"],
                       capture_output=True, timeout=6)
        net = True
    except Exception:
        net = False
    return {
        "python_docx": has("docx"),
        "jsonschema": has("jsonschema"),
        "jinja2": has("jinja2"),
        "bibtexparser": has("bibtexparser"),
        "latex_toolchain": has_bin("pdflatex") or has_bin("latexmk"),
        "pandoc": has_bin("pandoc"),
        "network": net,
    }


def ai_stub_s2(ir_path: str, workdir: str) -> str:
    """CLI 占位：把 S1 的 IR 直通为 rewritten IR（不执行真实学术改写）。"""
    ir = common.load_json(ir_path)
    ir["provenance"]["stage"] = "S2"
    ir["provenance"]["parser"] = "ai-stub@1.0.0"
    ir["rewrite_log"] = [{
        "source_ref": "ALL", "target_ref": "ALL",
        "change_type": "format_only",
        "rationale": "CLI demo 占位：真实改写由 Skill 提示词 02-academic-rewrite.md 执行",
        "risk": "high",
    }]
    out = os.path.join(workdir, "02-rewrite", "manuscript.rewritten.json")
    common.save_json_atomic(out, ir)
    return out


def ai_stub_s3(workdir: str, total_score: float) -> str:
    assessment = {
        "schema_version": "1.0",
        "assessed_at": common.utcnow_iso(),
        "total_score": total_score,
        "tier": "Q2" if total_score >= 7.5 else ("Q3" if total_score >= 6.5 else "Q4"),
        "dimensions": {
            "novelty": total_score, "methodological_rigor": total_score,
            "experimental_completeness": total_score, "academic_writing": total_score,
            "structural_compliance": total_score, "reproducibility": total_score,
        },
        "weakest_dimension": "experimental_completeness",
        "improvement_actions": [],
        "self_check": {
            "independent_of_rewrite_log": True,
            "all_dimensions_scored": True,
            "is_cli_stub": True,
            "note": "CLI 占位评估，真实评估由 Skill 提示词 03-quality-assessment.md 执行",
        },
        "input_summary": {
            "scope_tags": [], "method_tags": [],
        },
    }
    out = os.path.join(workdir, "03-assess", "assessment.json")
    common.save_json_atomic(out, assessment)
    return out


def main():
    ap = argparse.ArgumentParser(description="math-modeling-to-sci-skill pipeline")
    ap.add_argument("--input", help="输入文件路径 (.docx/.tex/.md)")
    ap.add_argument("--workdir", default="runs/demo")
    ap.add_argument("--mode", choices=["auto", "interactive", "dry-run"], default="auto")
    ap.add_argument("--stage", default="S1", choices=STAGES)
    ap.add_argument("--target-journal", default=None)
    ap.add_argument("--scope-tags", default="", help="逗号分隔，示例 applied-mathematics,optimization")
    ap.add_argument("--method-tags", default="", help="逗号分隔")
    ap.add_argument("--score", type=float, default=6.5, help="S3 占位总分（生产环境由 AI 评估）")
    ap.add_argument("--ai-stub", action="store_true", default=True)
    ap.add_argument("--no-ai-stub", dest="ai_stub", action="store_false")
    ap.add_argument("--probe-env", action="store_true", help="仅探测环境并退出")
    args = ap.parse_args()

    if args.probe_env:
        print(json.dumps(probe_env(), indent=2, ensure_ascii=False))
        return

    if not args.input:
        ap.error("--input 必填（除非 --probe-env）")
    if not os.path.isfile(args.input):
        ap.error(f"输入文件不存在: {args.input}")

    os.makedirs(args.workdir, exist_ok=True)
    logger = AuditLogger(args.workdir)
    logger.set_env(probe_env())

    start = STAGES.index(args.stage)
    # 若从 S4+ 开始但缺少上游产物，ingest/rewrite 仍按需补（仅 demo 便利）
    scope = [s for s in args.scope_tags.split(",") if s]
    method = [m for m in args.method_tags.split(",") if m]

    ir_path = os.path.join(args.workdir, "01-parse", "manuscript.ir.json")
    rewritten_path = os.path.join(args.workdir, "02-rewrite", "manuscript.rewritten.json")
    assessment_path = os.path.join(args.workdir, "03-assess", "assessment.json")
    jm_path = os.path.join(args.workdir, "04-journals", "journal-match.json")

    for i in range(start, len(STAGES)):
        stage = STAGES[i]
        if stage == "S1":
            ir_path = ingest.run(args.input, args.workdir)
        elif stage == "S2":
            if args.ai_stub:
                rewritten_path = ai_stub_s2(ir_path, args.workdir)
            else:
                print("[S2] 需由 Skill 提示词 02-academic-rewrite.md 执行；本 CLI 未提供 --ai-stub 时跳过。")
                continue
        elif stage == "S3":
            if args.ai_stub:
                assessment_path = ai_stub_s3(args.workdir, args.score)
            else:
                print("[S3] 需由 Skill 提示词 03-quality-assessment.md 执行。")
                continue
        elif stage == "S4":
            jm_path = journals.run(assessment_path, args.workdir,
                                   paper_scope=scope, paper_method=method,
                                   total_score=args.score, target_journal=args.target_journal)
        elif stage == "S5":
            render.run(rewritten_path, args.workdir, jm_path)
        elif stage == "S6":
            bib = os.path.join(args.workdir, "05-template", "build", "references.bib")
            jm = common.load_json(jm_path) if os.path.isfile(jm_path) else {}
            cons = ((jm.get("recommendations") or [{}])[0]).get("constraints", {})
            validate.run(rewritten_path, args.workdir, bib_path=bib if os.path.isfile(bib) else None,
                         constraints=cons, target_journal=args.target_journal)
        elif stage == "S7":
            report.run(args.workdir)

    logger.log("run_end", "S0", result="success", detail="pipeline finished (CLI)")
    print(f"\n✅ 流水线完成。工作目录：{args.workdir}")
    print(f"   报告：{os.path.join(args.workdir, 'conversion-report.md')}")


if __name__ == "__main__":
    main()
