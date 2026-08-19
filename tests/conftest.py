"""conftest.py — pytest 公共 fixture。把 scripts/ 加入 sys.path。"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import common  # noqa: E402  (确保脚本模块可导入)

SAMPLE_INPUT = os.path.join(REPO_ROOT, "examples", "input", "sample-modeling-report.tex")


def run_full_pipeline(workdir, score=7.2, scope=None, method=None):
    """在 workdir 跑通 S1→S7（CLI 占位模式），返回 workdir 路径。"""
    import ingest, journals, render, validate, report  # noqa: F401
    from audit import AuditLogger
    os.makedirs(workdir, exist_ok=True)
    AuditLogger(workdir).set_env({})
    ir = ingest.run(SAMPLE_INPUT, workdir)
    # S2 / S3 占位
    ms = common.load_json(ir)
    ms["provenance"]["stage"] = "S2"
    common.save_json_atomic(os.path.join(workdir, "02-rewrite", "manuscript.rewritten.json"), ms)
    assess = {
        "schema_version": "1.0", "total_score": score, "tier": "Q2",
        "dimensions": {k: score for k in ["novelty", "methodological_rigor",
                                           "experimental_completeness", "academic_writing",
                                           "structural_compliance", "reproducibility"]},
        "self_check": {"is_cli_stub": True},
        "input_summary": {"scope_tags": scope or [], "method_tags": method or []},
    }
    common.save_json_atomic(os.path.join(workdir, "03-assess", "assessment.json"), assess)
    jm = journals.run(os.path.join(workdir, "03-assess", "assessment.json"), workdir,
                      paper_scope=scope, paper_method=method, total_score=score)
    render.run(os.path.join(workdir, "02-rewrite", "manuscript.rewritten.json"), workdir, jm)
    bib = os.path.join(workdir, "05-template", "build", "references.bib")
    jmd = common.load_json(jm)
    cons = (jmd.get("recommendations") or [{}])[0].get("constraints", {})
    validate.run(os.path.join(workdir, "02-rewrite", "manuscript.rewritten.json"), workdir,
                 bib_path=bib if os.path.isfile(bib) else None, constraints=cons)
    report.run(workdir)
    return workdir
