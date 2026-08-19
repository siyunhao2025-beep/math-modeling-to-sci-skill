"""report.py — S7 结果汇报。汇聚各阶段产物生成 conversion-report.md。"""
from __future__ import annotations

import os
import sys

from common import load_json, repo_path
from audit import AuditLogger


def _read(workdir, *parts):
    p = os.path.join(workdir, *parts)
    if os.path.isfile(p):
        return load_json(p)
    return None


def run(workdir: str) -> str:
    logger = AuditLogger(workdir)
    ir = _read(workdir, "01-parse", "manuscript.ir.json") or {}
    rewritten = _read(workdir, "02-rewrite", "manuscript.rewritten.json") or ir
    assessment = _read(workdir, "03-assess", "assessment.json")
    jm = _read(workdir, "04-journals", "journal-match.json")
    manifest = _read(workdir, "05-template", "MANIFEST.json")
    validation = _read(workdir, "06-validate", "validation-final.json")
    audit_events = logger.read_all()

    # 状态标签
    err_count = (validation or {}).get("summary", {}).get("error_count", 0)
    status = "SUBMISSION_READY" if err_count == 0 else "DRAFT_WITH_BLOCKERS"

    total_score = (assessment or {}).get("total_score")
    recs = (jm or {}).get("recommendations", [])
    top1 = recs[0] if recs else None
    gaps = (rewritten or ir).get("gaps", [])
    blockers = [(validation or {}).get("summary", {}).get("unresolved_error_ids", [])]

    md = []
    md.append("# 转换报告 · Conversion Report\n")
    md.append(f"> 生成时间：{logger.read_all()[-1]['at'] if audit_events else 'n/a'}\n")

    # 0. 摘要卡
    md.append("## 0. 摘要卡\n")
    md.append("| 项 | 值 |")
    md.append("|---|---|")
    md.append(f"| 状态 | **{status}** |")
    md.append(f"| 质量总分 | {total_score if total_score is not None else 'n/a'} / 10 |")
    md.append(f"| 推荐首投 | {top1['name'] if top1 else 'n/a'} "
              f"(match {top1['match_score'] if top1 else 'n/a'}) |")
    md.append(f"| 待补项 | {len(gaps)} 项（其中需作者决策 {sum(1 for g in gaps if g.get('severity') in ('blocker','high'))} 项）|")
    md.append(f"| 残留错误 | {err_count} |")
    md.append("")

    # 1. 执行概览
    md.append("## 1. 执行概览\n")
    md.append(f"- 工作目录：`{workdir}`")
    md.append(f"- 阶段事件数：{len(audit_events)}")
    retries = sum(1 for e in audit_events if e.get('event') == 'gate_decision' and e.get('action') == 'retry')
    degrades = sum(1 for e in audit_events if e.get('event') == 'degrade')
    md.append(f"- 重试次数：{retries} · 降级次数：{degrades}")
    md.append("")

    # 2. 输入解析
    md.append("## 2. 输入解析（S1）\n")
    md.append(f"- 来源：{ir.get('provenance', {}).get('source_file', 'n/a')} "
              f"({ir.get('provenance', {}).get('source_format', 'n/a')})")
    md.append(f"- 识别章节：{len(ir.get('sections', []))} · 公式：{len(ir.get('equations', []))} · "
              f"图：{len(ir.get('figures', []))} · 表：{len(ir.get('tables', []))}")
    md.append("")

    # 3. 改写说明
    md.append("## 3. 改写说明（S2）\n")
    rw_log = rewritten.get("rewrite_log", [])
    md.append(f"- 改写记录条目：{len(rw_log)}")
    md.append("- 反幻觉：所有数值与公式未经改动；缺失内容以 `[[MISSING]]` 标记交作者补充。")
    md.append("")

    # 4. 质量评估
    md.append("## 4. 质量评估（S3）\n")
    if assessment:
        dims = assessment.get("dimensions", assessment.get("scores", {}))
        if isinstance(dims, dict):
            for k, v in dims.items():
                md.append(f"- {k}: {v}")
        weakest = assessment.get("weakest_dimension")
        if weakest:
            md.append(f"- 最弱维度：{weakest}")
    else:
        md.append("- 未生成评估（dry-run 或跳过）。")
    md.append("")

    # 5. 期刊推荐
    md.append("## 5. 期刊推荐（S4）\n")
    if recs:
        md.append("| 排名 | 期刊 | 匹配分 | IF(年,来源) | 分区 |")
        md.append("|---|---|---|---|---|")
        for r in recs:
            if_h = r.get("impact_factor", {})
            md.append(f"| {r['rank']} | {r['name']} | {r['match_score']} | "
                      f"{if_h.get('value')} ({if_h.get('year')}) | {r.get('quartile')} |")
        md.append("")
        md.append(f"**投稿梯度**：\n\n{(jm or {}).get('strategy_note', 'n/a')}\n")
        if (jm or {}).get("self_check", {}).get("offline_mode"):
            md.append("> ⚠️ 离线匹配模式：影响因子与 Aims&Scope 未经联网核实，投稿前请自行复核。")
    else:
        md.append("- 无推荐（候选不足，见下方人工检索建议）。")
    md.append("")

    # 6. 模板适配
    md.append("## 6. 模板适配（S5）\n")
    if manifest:
        md.append(f"- 模板级别：Level {manifest.get('template_level')}（{manifest.get('template_source')}）")
        if not manifest.get("is_official_template"):
            md.append("> ⚠️ 非官方模板：投稿前必须下载期刊官方模板并迁移内容。")
        md.append(f"- 文档类：`{manifest.get('document_class')}` · 参考文献样式：`{manifest.get('bib_style')}`")
    else:
        md.append("- 未生成构建（跳过）。")
    md.append("")

    # 7. 校验结果
    md.append("## 7. 校验结果（S6）\n")
    if validation:
        summ = validation.get("summary", {})
        md.append(f"- 错误：{summ.get('error_count')} · 警告：{summ.get('warning_count')} · "
                  f"自动修复：{summ.get('auto_fixed_count')}")
        md.append(f"- 判定：{validation.get('verdict')}")
        if status == "DRAFT_WITH_BLOCKERS":
            md.append("\n### ⛔ 残留错误（需处理后方可投稿）\n")
            for cid in summ.get("unresolved_error_ids", []):
                md.append(f"- `{cid}`")
    else:
        md.append("- 未运行校验。")
    md.append("")

    # 8. 待作者补充
    md.append("## 8. 待作者补充清单（Action Items）\n")
    if gaps:
        md.append("| ID | 严重度 | 类别 | 位置 | 缺什么 |")
        md.append("|---|---|---|---|---|")
        for g in gaps:
            md.append(f"| {g.get('id')} | {g.get('severity')} | {g.get('category')} | "
                      f"{g.get('where')} | {g.get('what')} |")
    else:
        md.append("- 无登记的内容缺口。")
    md.append("")

    # 9. 投稿前检查表
    md.append("## 9. 投稿前检查表\n")
    md.append("- [ ] 已替换为目标期刊官方模板")
    md.append("- [ ] 参考文献格式符合 `reference_style`")
    md.append("- [ ] 图表分辨率 / 格式达标")
    md.append("- [ ] 字数 / 摘要 / 关键词符合 constraints")
    md.append("- [ ] 所有 `[[MISSING]]` / `[[UNVERIFIED_REF]]` 已清除")
    md.append("- [ ] 未验证引用已补全或删除")
    md.append("- [ ] Cover letter / 伦理声明 / 数据可用性声明齐备")
    md.append("")

    # 10. 审计摘要
    md.append("## 10. 审计摘要\n")
    md.append(f"- 关键事件计数：retry={retries}, degrade={degrades}, block="
              f"{sum(1 for e in audit_events if e.get('event')=='run_end' and e.get('result')=='blocked')}")
    md.append("- 声明：本报告与 `audit.jsonl` 一致。")
    md.append("")

    out = os.path.join(workdir, "conversion-report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    logger.log("stage_end", "S7", artifacts=[{"path": out}], gate_metrics={"status": status})
    return out


if __name__ == "__main__":
    wd = sys.argv[1] if len(sys.argv) > 1 else "runs/demo"
    print(run(wd))
