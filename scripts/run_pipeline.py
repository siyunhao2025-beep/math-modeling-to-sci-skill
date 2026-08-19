"""run_pipeline.py — S1→S7 runtime with executable gates and S8 bridge.

The CLI has three explicit execution layers:
- deterministic S1/S4/S5/S6/S7 runtime + G1-G6 gate enforcement;
- Agent-produced S2 rewrite and S3 assessment artifacts;
- logical post-S6 S8 Publication Readiness checks before the final S7 report.

For demos, ``--ai-stub`` (default) creates conservative S2/S3 placeholders and
S8 is not auto-run. ``--no-ai-stub`` never pretends to call an LLM: it requires
real S2/S3 artifacts already written by the Agent Skill. With real artifacts,
``--readiness auto`` attempts deterministic S8 checks and lets the final report
surface unresolved blockers; ``--readiness required`` returns non-zero unless
the preflight reaches READY_FOR_HUMAN_SUBMISSION_CHECK.
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
from gates import GateEvaluator
import ingest, journals, render, validate, report
from readiness.pipeline_bridge import run_from_workdir as run_readiness_from_workdir

STAGES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]
GATE_BY_STAGE = {f"S{i}": f"G{i}" for i in range(1, 7)}
PIPELINE_YAML = common.repo_path("config", "pipeline.yaml")
READY_STATUS = "READY_FOR_HUMAN_SUBMISSION_CHECK"


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
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import urllib.request,socket;"
                "socket.setdefaulttimeout(3);"
                "urllib.request.urlopen('https://api.crossref.org')",
            ],
            capture_output=True,
            timeout=6,
        )
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


def snapshot_input(input_path: str, workdir: str) -> str:
    target_dir = os.path.join(workdir, "00-input")
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(input_path))
    if os.path.abspath(input_path) != os.path.abspath(target):
        shutil.copy2(input_path, target)
    return target


def ai_stub_s2(ir_path: str, workdir: str) -> str:
    """Demo-only pass-through. It does not perform academic rewriting."""
    ir = common.load_json(ir_path)
    ir["provenance"]["stage"] = "S2"
    ir["provenance"]["upstream_sha256"] = common.sha256_of(ir_path)
    ir["provenance"]["parser"] = "cli-demo-stub@1.2.0"
    ir["rewrite_log"] = [{
        "source_ref": "ALL",
        "target_ref": "ALL",
        "change_type": "format_only",
        "rationale": (
            "CLI demo stub only: scientific content was passed through unchanged. "
            "A real rewrite must be produced by prompts/02-academic-rewrite.md."
        ),
        "risk": "high",
    }]
    out = os.path.join(workdir, "02-rewrite", "manuscript.rewritten.json")
    common.save_json_atomic(out, ir)
    return out


def _stub_tier(score: float) -> str:
    if score >= 8.0:
        return "Q1-ready"
    if score >= 7.0:
        return "Q2-ready"
    if score >= 6.5:
        return "Q3-Q4-ready"
    if score >= 5.0:
        return "major-revision-needed"
    return "not-ready"


def ai_stub_s3(
    rewritten_path: str,
    workdir: str,
    total_score: float,
    scope: list[str],
    method: list[str],
) -> str:
    """Create a schema-valid demo assessment without pretending it is expert review."""
    ms = common.load_json(rewritten_path)
    evidence = next((s.get("id") for s in ms.get("sections", []) if s.get("id")), "sec-1")
    dim_names = [
        "novelty",
        "methodological_rigor",
        "experimental_completeness",
        "academic_writing",
        "structural_compliance",
        "reproducibility",
    ]
    dims = {
        name: {
            "score": total_score,
            "justification": (
                "CLI demo placeholder score only; no independent scholarly assessment "
                "has been performed for this dimension."
            ),
            "evidence_refs": [evidence],
        }
        for name in dim_names
    }
    assessment = {
        "schema_version": "1.0",
        "assessed_at": common.utcnow_iso(),
        "target_ir_sha256": common.sha256_of(rewritten_path) or "",
        "assessor_note": (
            "CLI demo stub. Replace this artifact with a real independent S3 assessment "
            "before treating the manuscript as submission-ready."
        ),
        "dimensions": dims,
        "total_score": total_score,
        "score_breakdown": "CLI demo: all six dimensions assigned the same placeholder score.",
        "tier": _stub_tier(total_score),
        "confidence": 0.5,
        "improvement_actions": [],
        "field_classification": {
            "primary_field": None,
            "secondary_fields": [],
            "scope_tags": scope,
            "method_tags": method,
            "application_domain": None,
            "msc_suggestions": [],
        },
        "caveats": [
            "This is a deterministic CLI demo assessment, not an AI or human peer review."
        ],
        "self_check": {
            "all_dimensions_have_evidence": True,
            "score_arithmetic_verified": True,
            "no_fabricated_claims": True,
            "actions_are_specific": True,
            "notes": "Schema-valid placeholder generated by --ai-stub.",
        },
    }
    out = os.path.join(workdir, "03-assess", "assessment.json")
    common.save_json_atomic(out, assessment)
    return out


def print_audit(workdir: str) -> int:
    logger = AuditLogger(workdir)
    events = logger.read_all()
    if not events:
        print(f"No audit events found in {os.path.join(workdir, 'audit.jsonl')}")
        return 1
    print(json.dumps(events, ensure_ascii=False, indent=2))
    return 0


def _existing(path: str, label: str) -> str:
    if not os.path.isfile(path):
        raise RuntimeError(f"{label} missing: {path}")
    return path


def _stage_config(pipeline_cfg: dict, stage: str) -> dict:
    for item in pipeline_cfg.get("stages", []):
        if item.get("id") == stage:
            return item
    return {}


def _gate_failure_action(result: dict, mode: str) -> tuple[str, str]:
    cfg = result.get("on_fail") or {}
    action = cfg.get("action", "block")
    if action == "ask_human":
        if mode == "interactive":
            return "ask_human", "configured human checkpoint"
        return cfg.get("fallback_action", "block"), "auto-mode fallback from ask_human"
    return action, "configured on_fail action"


def _interactive_confirm(message: str) -> bool:
    if not sys.stdin.isatty():
        raise RuntimeError("interactive mode requires a TTY")
    answer = input(f"{message} [Y/n] ").strip().lower()
    return answer in ("", "y", "yes")


def _report_gate(result: dict) -> None:
    status = "PASS" if result.get("passed") else "FAIL"
    print(f"[{result['gate']}] {status} — {result.get('name')}")
    for item in result.get("error_failures", []):
        print(f"  ERROR {item['id']} {item['check']}: {item['detail']}")
    for item in result.get("warnings", []):
        print(f"  WARN  {item['id']} {item['check']}: {item['detail']}")


def _run_s8_if_requested(args, logger: AuditLogger) -> tuple[str | None, str | None]:
    """Run the deterministic readiness bridge before S7 and return status/error."""
    if args.readiness == "off":
        logger.log("skip", "S8", result="skipped", detail="--readiness off")
        return None, None

    if args.ai_stub:
        detail = "S8 auto-run skipped because S2/S3 are demo stubs, not real Agent artifacts"
        logger.log("degrade", "S8", result="demo_only", detail=detail)
        if args.readiness == "required":
            return None, detail
        return None, None

    validation_path = os.path.join(args.workdir, "06-validate", "validation-final.json")
    if not os.path.isfile(validation_path):
        detail = "S8 requires completed S6 validation-final.json"
        logger.log("skip", "S8", result="missing_prerequisite", detail=detail)
        if args.readiness == "required":
            return None, detail
        return None, None

    print("\n[S8] Publication Readiness — resolving S1-S7 artifacts automatically")
    try:
        preflight = run_readiness_from_workdir(
            args.workdir,
            target_journal=args.target_journal,
            with_similarity_precheck=args.similarity_precheck,
        )
    except Exception as exc:
        detail = f"S8 readiness bridge failed: {exc}"
        logger.log("error", "S8", result="failed", detail=detail)
        return None, detail if args.readiness == "required" else None

    status = preflight.get("status")
    logger.log(
        "stage_end",
        "S8",
        result=status,
        artifacts=[{"path": os.path.join(args.workdir, "08-readiness", "submission-preflight.json")}],
        detail=(
            "Deterministic S8 bridge ran. Agent-only semantic citation support, visual "
            "scientific review and Reviewer Simulator remain required where absent."
        ),
    )
    print(f"[S8] preflight={status}")
    if args.readiness == "required" and status != READY_STATUS:
        return status, f"S8 required but preflight={status}"
    return status, None


def main() -> int:
    ap = argparse.ArgumentParser(description="math-modeling-to-sci-skill pipeline")
    ap.add_argument("--input", help="input manuscript (.docx/.tex/.zip/.md); required when S1 runs")
    ap.add_argument("--workdir", default="runs/demo")
    ap.add_argument("--mode", choices=["auto", "interactive", "dry-run"], default="auto")
    ap.add_argument("--stage", default="S1", choices=STAGES, help="first legacy stage to run")
    ap.add_argument("--stop-after", choices=STAGES, default=None, help="last legacy stage to run")
    ap.add_argument("--target-journal", "--journal", dest="target_journal", default=None)
    ap.add_argument("--scope-tags", default="", help="comma-separated scope tags")
    ap.add_argument("--method-tags", default="", help="comma-separated method tags")
    ap.add_argument("--score", type=float, default=6.5, help="S3 demo score used only by --ai-stub")
    ap.add_argument(
        "--readiness",
        choices=["auto", "required", "off"],
        default="auto",
        help=(
            "post-S6 S8 behavior: auto=run deterministic readiness before S7 with real Agent "
            "artifacts, required=also fail unless preflight is READY_FOR_HUMAN_SUBMISSION_CHECK, "
            "off=skip S8"
        ),
    )
    ap.add_argument(
        "--similarity-precheck",
        action="store_true",
        help="include advisory Semantic Scholar similarity discovery during S8 (not Turnitin/iThenticate)",
    )
    ai = ap.add_mutually_exclusive_group()
    ai.add_argument("--ai-stub", dest="ai_stub", action="store_true",
                    help="generate demo-only S2/S3 placeholders (default)")
    ai.add_argument("--no-ai-stub", dest="ai_stub", action="store_false",
                    help="consume real S2/S3 artifacts already present in workdir; does not call an LLM")
    ap.set_defaults(ai_stub=True)
    ap.add_argument("--probe-env", action="store_true", help="probe environment and exit")
    ap.add_argument("--show-audit", action="store_true", help="print workdir/audit.jsonl and exit")
    args = ap.parse_args()

    if args.probe_env:
        print(json.dumps(probe_env(), indent=2, ensure_ascii=False))
        return 0
    if args.show_audit:
        return print_audit(args.workdir)

    pipeline_cfg = common.load_yaml(PIPELINE_YAML)
    mode_cfg = ((pipeline_cfg.get("pipeline") or {}).get("modes") or {}).get(args.mode, {})

    start = STAGES.index(args.stage)
    stop_stage = args.stop_after
    if args.mode == "dry-run":
        configured = mode_cfg.get("stages") or ["S1", "S2", "S3", "S4"]
        dry_last = max(STAGES.index(x) for x in configured)
        if stop_stage is None or STAGES.index(stop_stage) > dry_last:
            stop_stage = STAGES[dry_last]
    if stop_stage is None:
        stop_stage = "S7"
    stop = STAGES.index(stop_stage)
    if stop < start:
        ap.error("--stop-after cannot be earlier than --stage")

    if start == 0:
        if not args.input:
            ap.error("--input is required when S1 runs")
        if not os.path.isfile(args.input):
            ap.error(f"input file does not exist: {args.input}")

    os.makedirs(args.workdir, exist_ok=True)
    logger = AuditLogger(args.workdir)
    logger.set_env({
        **probe_env(),
        "mode": args.mode,
        "ai_stub": args.ai_stub,
        "readiness": args.readiness,
        "pipeline_config_version": (pipeline_cfg.get("pipeline") or {}).get("version"),
    })
    if args.ai_stub:
        logger.log(
            "degrade",
            "S0",
            result="demo_only",
            detail=(
                "AI stub mode is active. S2/S3 are placeholders; final output must not be "
                "treated as a real submission-ready manuscript."
            ),
        )

    source_path = args.input
    if start == 0:
        source_path = snapshot_input(args.input, args.workdir)

    scope = [x.strip() for x in args.scope_tags.split(",") if x.strip()]
    method = [x.strip() for x in args.method_tags.split(",") if x.strip()]

    ir_path = os.path.join(args.workdir, "01-parse", "manuscript.ir.json")
    rewritten_path = os.path.join(args.workdir, "02-rewrite", "manuscript.rewritten.json")
    assessment_path = os.path.join(args.workdir, "03-assess", "assessment.json")
    jm_path = os.path.join(args.workdir, "04-journals", "journal-match.json")

    blocked = False
    block_detail = None
    readiness_status = None

    for idx in range(start, stop + 1):
        stage = STAGES[idx]
        cfg = _stage_config(pipeline_cfg, stage)
        attempts = 0
        max_attempts = int(((cfg.get("retry") or {}).get("max_attempts") or 1))

        while True:
            attempts += 1
            print(f"\n[{stage}] {cfg.get('name', stage)} — attempt {attempts}")

            if stage == "S1":
                ir_path = ingest.run(args.input, args.workdir)

            elif stage == "S2":
                _existing(ir_path, "S1 IR")
                if args.ai_stub:
                    rewritten_path = ai_stub_s2(ir_path, args.workdir)
                else:
                    _existing(
                        rewritten_path,
                        "real S2 artifact (run prompts/02-academic-rewrite.md first)",
                    )
                    print(f"[S2] using existing real artifact: {rewritten_path}")

            elif stage == "S3":
                _existing(rewritten_path, "S2 rewritten IR")
                if args.ai_stub:
                    assessment_path = ai_stub_s3(
                        rewritten_path, args.workdir, args.score, scope, method
                    )
                else:
                    _existing(
                        assessment_path,
                        "real S3 artifact (run prompts/03-quality-assessment.md first)",
                    )
                    print(f"[S3] using existing real artifact: {assessment_path}")

            elif stage == "S4":
                _existing(assessment_path, "S3 assessment")
                jm_path = journals.run(
                    assessment_path,
                    args.workdir,
                    paper_scope=scope,
                    paper_method=method,
                    total_score=args.score if args.ai_stub else None,
                    target_journal=args.target_journal,
                )

            elif stage == "S5":
                _existing(rewritten_path, "S2 rewritten IR")
                _existing(jm_path, "S4 journal match")
                render.run(rewritten_path, args.workdir, jm_path)

            elif stage == "S6":
                _existing(rewritten_path, "S2 rewritten IR")
                _existing(jm_path, "S4 journal match")
                main_tex = os.path.join(args.workdir, "05-template", "build", "main.tex")
                _existing(main_tex, "S5 build/main.tex")
                bib = os.path.join(args.workdir, "05-template", "build", "references.bib")
                jm = common.load_json(jm_path)
                cons = ((jm.get("recommendations") or [{}])[0]).get("constraints", {})
                validate.run(
                    rewritten_path,
                    args.workdir,
                    bib_path=bib if os.path.isfile(bib) else None,
                    constraints=cons,
                    round_no=attempts,
                    target_journal=args.target_journal,
                )

            elif stage == "S7":
                readiness_status, readiness_error = _run_s8_if_requested(args, logger)
                if readiness_error:
                    blocked = True
                    block_detail = readiness_error
                    logger.log("run_end", "S8", result="blocked", detail=readiness_error)
                else:
                    report.run(args.workdir)

            gate_id = GATE_BY_STAGE.get(stage)
            if not gate_id:
                break

            gate = GateEvaluator(args.workdir, source_path=source_path).evaluate(gate_id)
            _report_gate(gate)
            logger.log(
                "gate_decision",
                stage,
                gate=gate_id,
                result="pass" if gate["passed"] else "fail",
                action="proceed" if gate["passed"] else None,
                gate_metrics={
                    "error_failures": len(gate.get("error_failures", [])),
                    "warnings": len(gate.get("warnings", [])),
                    "attempt": attempts,
                },
            )

            if gate["passed"]:
                if args.mode == "interactive" and not _interactive_confirm(
                    f"{gate_id} passed. Continue after {stage}?"
                ):
                    blocked = True
                    block_detail = f"user stopped after {gate_id}"
                break

            action, reason = _gate_failure_action(gate, args.mode)
            if action == "ask_human":
                if _interactive_confirm(f"{gate_id} failed. Continue in degraded mode?"):
                    action = "degrade"
                else:
                    action = "block"

            if action == "retry" and attempts < max_attempts:
                logger.log(
                    "gate_decision",
                    stage,
                    gate=gate_id,
                    result="fail",
                    action="retry",
                    detail=reason,
                )
                continue

            if action == "retry":
                after = ((gate.get("on_fail") or {}).get("after_exhausted") or {})
                action = after.get("action", "block")

            if action == "degrade":
                logger.log(
                    "degrade",
                    stage,
                    gate=gate_id,
                    result="degraded",
                    detail=reason,
                )
                print(f"[{gate_id}] continuing with explicit DEGRADE disclosure")
                break

            if action == "rollback":
                block_detail = (
                    f"{gate_id} requested rollback to "
                    f"{(gate.get('on_fail') or {}).get('rollback_to', 'an upstream stage')}; "
                    "the CLI cannot perform semantic rewriting. Run the Agent prompt, then resume."
                )
            else:
                block_detail = f"{gate_id} blocked the pipeline ({reason})"
            blocked = True
            logger.log("run_end", stage, result="blocked", detail=block_detail, gate=gate_id)
            break

        if blocked:
            break

    if blocked:
        if args.mode != "dry-run":
            try:
                report_path = report.run(args.workdir)
                print(f"\n⛔ Pipeline blocked. Diagnostic report: {report_path}")
            except Exception as exc:
                print(f"\n⛔ Pipeline blocked; partial report could not be generated: {exc}")
        else:
            print(f"\n⛔ Dry-run blocked: {block_detail}")
        return 2

    logger.log("run_end", "S0", result="success", detail="requested stage range finished")
    print(f"\n✅ Requested pipeline range finished: {args.stage} → {stop_stage}")
    print(f"   workdir: {args.workdir}")
    if stop >= STAGES.index("S7"):
        print(f"   report: {os.path.join(args.workdir, 'conversion-report.md')}")
        if readiness_status:
            print(f"   S8 preflight: {readiness_status}")
    if args.ai_stub:
        print("   NOTE: --ai-stub was used; this run is DEMO ONLY, not a real submission-ready assessment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
