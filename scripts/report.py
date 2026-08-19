"""report.py — S7 result report built from auditable artifacts."""
from __future__ import annotations

import os
import sys

from common import load_json
from audit import AuditLogger


def _read(workdir, *parts):
    p = os.path.join(workdir, *parts)
    if os.path.isfile(p):
        return load_json(p)
    return None


def _run_state(audit_events: list[dict], assessment: dict | None, validation: dict | None) -> tuple[str, list[str]]:
    """Return a conservative manuscript status and the reasons behind it."""
    reasons: list[str] = []
    blocked = any(e.get("result") == "blocked" for e in audit_events)
    demo_only = any(e.get("result") == "demo_only" for e in audit_events)
    assessor_note = str((assessment or {}).get("assessor_note") or "").lower()
    if "demo stub" in assessor_note or "demo placeholder" in assessor_note:
        demo_only = True

    if validation is None:
        reasons.append("S6 validation-final.json is missing")
    else:
        err = (validation.get("summary") or {}).get("error_count")
        if not isinstance(err, int):
            reasons.append("S6 validation error_count is missing or invalid")
        elif err > 0:
            reasons.append(f"S6 has {err} unresolved error(s)")
        if validation.get("verdict") not in ("PASS", "PASS_WITH_WARNINGS"):
            reasons.append(f"S6 verdict is {validation.get('verdict')}")

    if blocked:
        reasons.append("the runtime recorded a blocking gate decision")
    if demo_only:
        reasons.append("--ai-stub/demo placeholders were used for S2/S3")

    if demo_only:
        return "DEMO_ONLY_NOT_SUBMISSION_READY", reasons
    if reasons:
        return "DRAFT_WITH_BLOCKERS", reasons
    return "SUBMISSION_READY", []


def run(workdir: str) -> str:
    logger = AuditLogger(workdir)
    ir = _read(workdir, "01-parse", "manuscript.ir.json") or {}
    rewritten = _read(workdir, "02-rewrite", "manuscript.rewritten.json") or ir
    assessment = _read(workdir, "03-assess", "assessment.json")
    jm = _read(workdir, "04-journals", "journal-match.json")
    manifest = _read(workdir, "05-template", "MANIFEST.json")
    validation = _read(workdir, "06-validate", "validation-final.json")
    audit_events = logger.read_all()

    status, status_reasons = _run_state(audit_events, assessment, validation)
    err_count = (validation or {}).get("summary", {}).get("error_count")
    if not isinstance(err_count, int):
        err_count = None

    total_score = (assessment or {}).get("total_score")
    recs = (jm or {}).get("recommendations", [])
    top1 = recs[0] if recs else None
    gaps = (rewritten or ir).get("gaps", [])

    md = []
    md.append("# 转换报告 · Conversion Report\n")
    md.append(f"> 生成时间：{audit_events[-1]['at'] if audit_events else 'n/a'}\n")

    if status != "SUBMISSION_READY":
        md.append("## ⛔ 状态说明\n")
        md.append(f"**{status}** — 本文件不得被解释为已通过投稿前质量门控。\n")
        for reason in status_reasons:
            md.append(f"- {reason}")
        md.append("")

    md.append("## 0. 摘要卡\n")
    md.append("| 项 | 值 |")
    md.append("|---|---|")
    md.append(f"| 状态 | **{status}** |")
    md.append(f"| 质量总分 | {total_score if total_score is not None else 'n/a'} / 10 |")
    md.append(
        f"| 推荐首投 | {top1['name'] if top1 else 'n/a'} "
        f"(match {top1['match_score'] if top1 else 'n/a'}) |"
    )
    md.append(
        f"| 待补项 | {len(gaps)} 项（其中需作者决策 "
        f"{sum(1 for g in gaps if g.get('severity') in ('blocker','high'))} 项）|"
    )
    md.append(f"| 残留错误 | {err_count if err_count is not None else 'n/a'} |")
    md.append("")

    md.append("## 1. 执行概览\n")
    md.append(f"- 工作目录：`{workdir}`")
    md.append(f"- 阶段事件数：{len(audit_events)}")
    retries = sum(
        1 for e in audit_events
        if e.get("event") == "gate_decision" and e.get("action") == "retry"
    )
    degrades = sum(1 for e in audit_events if e.get("event") == "degrade")
    blocks = sum(1 for e in audit_events if e.get("result") == "blocked")
    md.append(f"- 重试次数：{retries} · 降级次数：{degrades} · 阻塞事件：{blocks}")
    md.append("")

    md.append("## 2. 输入解析（S1）\n")
    md.append(
        f"- 来源：{ir.get('provenance', {}).get('source_file', 'n/a')} "
        f"({ir.get('provenance', {}).get('source_format', 'n/a')})"
    )
    md.append(
        f"- 识别章节：{len(ir.get('sections', []))} · 公式：{len(ir.get('equations', []))} · "
        f"图：{len(ir.get('figures', []))} · 表：{len(ir.get('tables', []))}"
    )
    md.append("")

    md.append("## 3. 改写说明（S2）\n")
    rw_log = rewritten.get("rewrite_log", [])
    md.append(f"- 改写记录条目：{len(rw_log)}")
    if any(e.get("result") == "demo_only" for e in audit_events):
        md.append("- ⚠️ 本次使用 CLI demo stub；S2 未执行真实学术化改写。")
    else:
        md.append("- 数值、公式和新增引用仍须以 G2 的实际门控结果为准，不以报告文字代替校验。")
    md.append("")

    md.append("## 4. 质量评估（S3）\n")
    if assessment:
        dims = assessment.get("dimensions", {})
        for key, value in dims.items():
            score = value.get("score") if isinstance(value, dict) else value
            md.append(f"- {key}: {score}")
        if assessment.get("assessor_note"):
            md.append(f"- 评估说明：{assessment['assessor_note']}")
    else:
        md.append("- 未生成评估。")
    md.append("")

    md.append("## 5. 期刊推荐（S4）\n")
    if recs:
        md.append("| 排名 | 期刊 | 匹配分 | IF(年,来源) | 分区 |")
        md.append("|---|---|---|---|---|")
        for r in recs:
            if_h = r.get("impact_factor", {})
            md.append(
                f"| {r['rank']} | {r['name']} | {r['match_score']} | "
                f"{if_h.get('value')} ({if_h.get('year')}, {if_h.get('source')}) | "
                f"{r.get('quartile')} |"
            )
        md.append("")
        md.append(f"**投稿梯度**：\n\n{(jm or {}).get('strategy_note', 'n/a')}\n")
        if (jm or {}).get("self_check", {}).get("offline_mode"):
            md.append(
                "> ⚠️ 离线匹配模式：影响因子、Aims & Scope、APC 等时效信息未经实时核实，"
                "正式投稿前必须在线复核。"
            )
    else:
        md.append("- 无推荐或 S4 尚未完成。")
    md.append("")

    md.append("## 6. 模板适配（S5）\n")
    if manifest:
        md.append(
            f"- 模板级别：Level {manifest.get('template_level')}"
            f"（{manifest.get('template_source')}）"
        )
        if not manifest.get("is_official_template"):
            md.append("> ⚠️ 非官方模板：投稿前必须下载期刊官方模板并重新核对格式。")
        md.append(
            f"- 文档类：`{manifest.get('document_class')}` · "
            f"参考文献样式：`{manifest.get('bib_style')}`"
        )
    else:
        md.append("- 未生成构建。")
    md.append("")

    md.append("## 7. 校验结果（S6）\n")
    if validation:
        summ = validation.get("summary", {})
        md.append(
            f"- 错误：{summ.get('error_count')} · 警告：{summ.get('warning_count')} · "
            f"自动修复：{summ.get('auto_fixed_count')}"
        )
        md.append(f"- 判定：{validation.get('verdict')}")
        if summ.get("unresolved_error_ids"):
            md.append("\n### ⛔ 残留错误\n")
            for cid in summ.get("unresolved_error_ids", []):
                md.append(f"- `{cid}`")
    else:
        md.append("- 未运行校验；因此不能标记为 SUBMISSION_READY。")
    md.append("")

    md.append("## 8. 待作者补充清单（Action Items）\n")
    if gaps:
        md.append("| ID | 严重度 | 类别 | 位置 | 缺什么 |")
        md.append("|---|---|---|---|---|")
        for g in gaps:
            md.append(
                f"| {g.get('id')} | {g.get('severity')} | {g.get('category')} | "
                f"{g.get('where')} | {g.get('what')} |"
            )
    else:
        md.append("- 无登记的内容缺口；这不等于研究内容已被证明完整。")
    md.append("")

    md.append("## 9. 投稿前检查表\n")
    md.append("- [ ] 已使用真实 S2/S3 产物，而非 CLI demo stub")
    md.append("- [ ] G1–G6 实际执行并通过，或所有降级/阻塞项均已处理")
    md.append("- [ ] 已替换为目标期刊当前官方模板")
    md.append("- [ ] 期刊时效信息已从官方来源重新核验")
    md.append("- [ ] 参考文献、图表、公式、数值和正文双向一致")
    md.append("- [ ] 所有 `[[MISSING]]` / `[[UNVERIFIED_REF]]` 已妥善处理")
    md.append("- [ ] Cover letter / 声明 / 数据与代码可用性材料齐备")
    md.append("")

    md.append("## 10. 审计摘要\n")
    md.append(f"- 关键事件计数：retry={retries}, degrade={degrades}, block={blocks}")
    md.append("- 状态由实际产物和 audit.jsonl 保守推导；CLI demo 不会被标记为可投稿。")
    md.append("")

    out = os.path.join(workdir, "conversion-report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    logger.log("stage_end", "S7", artifacts=[{"path": out}], gate_metrics={"status": status})
    return out


if __name__ == "__main__":
    wd = sys.argv[1] if len(sys.argv) > 1 else "runs/demo"
    print(run(wd))
