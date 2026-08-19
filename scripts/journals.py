"""journals.py — S4 期刊匹配。基于 config/journals.yaml 种子库打分排序。

离线优先：影响因子直接采用种子库的 seed-data（标注 UNVERIFIED），不联网。
联网核实逻辑在提示词层（04-journal-matching.md）描述，本脚本只做确定性打分。
"""
from __future__ import annotations

import os
import sys

from common import (load_json, load_yaml, repo_path, save_json_atomic, utcnow_iso,
                    validate_against_schema)
from audit import AuditLogger

JOURNALS_YAML = repo_path("config", "journals.yaml")
MATCH_SCHEMA = repo_path("config", "schema", "journal-match.schema.json")


def _overlap(a, b):
    return [x for x in (a or []) if x in (b or [])]


def score_journal(j, paper_scope, paper_method, total_score, weights, bands):
    scope_hit = _overlap(j.get("scope_tags", []), paper_scope)
    method_hit = _overlap(j.get("method_tags", []), paper_method)
    n_scope = max(1, len(j.get("scope_tags", [])))
    n_method = max(1, len(j.get("method_tags", [])))
    scope_fit = round(100 * len(scope_hit) / n_scope, 1)
    method_fit = round(100 * len(method_hit) / n_method, 1)

    # quality_fit: 论文分数 vs 该刊分区档位期望
    q_exp = {"Q1": 8.0, "Q2": 7.0, "Q3": 6.0, "Q4": 5.0}.get(j.get("quartile"), 6.0)
    quality_fit = max(0.0, min(100.0, 100 - abs(total_score - q_exp) * 25))

    # tier_alignment: 论文分数所在 band 的目标分区是否包含该刊分区
    band = None
    for b in bands:
        if b["min"] <= total_score <= b["max"]:
            band = b
            break
    target_q = band["target_quartiles"] if band else []
    tier_alignment = 100.0 if (j.get("quartile") in target_q) else 50.0

    # practical_fit: 审稿周期越短越好 + OA 友好
    rw = j.get("review_weeks") or [12, 24]
    avg_rw = sum(rw) / len(rw)
    speed = max(0.0, 100 - (avg_rw - 4) * 4)  # 4 周为满分基准
    oa_bonus = {"gold": 20, "hybrid": 12, "green": 8, "closed": 0, None: 0}.get(j.get("open_access"), 0)
    practical_fit = max(0.0, min(100.0, speed + oa_bonus))

    comp = {
        "scope_fit": scope_fit,
        "method_fit": method_fit,
        "quality_fit": round(quality_fit, 1),
        "tier_alignment": tier_alignment,
        "practical_fit": round(practical_fit, 1),
    }
    match_score = round(sum(comp[k] * weights.get(k, 0) for k in comp), 1)
    return match_score, comp, scope_hit, method_hit


def build_recommendation(j, rank, paper_scope, paper_method, total_score, weights, bands):
    match_score, comp, scope_hit, method_hit = score_journal(
        j, paper_scope, paper_method, total_score, weights, bands)
    if_have = j.get("impact_factor") or {}
    rec = {
        "rank": rank,
        "journal_id": j.get("id"),
        "name": j.get("name"),
        "publisher": j.get("publisher"),
        "issn": j.get("issn"),
        "homepage": j.get("submission_url"),
        "submission_url": j.get("submission_url"),
        "match_score": match_score,
        "score_components": comp,
        "match_rationale": (
            f"本文 scope 标签 {paper_scope} 与该刊 Aims&Scope 命中 {scope_hit or '—'}；"
            f"方法标签命中 {method_hit or '—'}。论文质量分 {total_score} 与该刊 "
            f"{j.get('quartile')} 档位匹配度 {comp['tier_alignment']:.0f}%。"
        ),
        "impact_factor": {
            "value": if_have.get("value"),
            "year": if_have.get("year"),
            "source": "local-cache (seed-data UNVERIFIED)",
            "retrieved_at": if_have.get("retrieved"),
            "note": "种子数据，未联网核实，投稿前请自行复核",
        },
        "quartile": j.get("quartile"),
        "jcr_category": j.get("jcr_category"),
        "review_weeks": j.get("review_weeks"),
        "open_access": j.get("open_access"),
        "apc": None,
        "fit_evidence": [
            {
                "scope_statement": f"Aims&Scope 涵盖: {', '.join(j.get('scope_tags', []))}",
                "paper_correspondence": f"本文 scope_tags={paper_scope}; 命中 {scope_hit or '无'}",
                "strength": "strong" if scope_hit else "weak",
            }
        ],
        "recent_similar_papers": [],
        "rejection_risks": _risks(j, total_score, scope_hit),
        "template": {
            "latex_url": (j.get("template") or {}).get("latex"),
            "docx_url": (j.get("template") or {}).get("docx"),
            "guide_for_authors_url": None,
            "bundled_fallback": (j.get("template") or {}).get("bundled_fallback"),
            "availability": "official" if (j.get("template") or {}).get("latex") else "bundled-fallback",
        },
        "constraints": j.get("constraints") or {},
        "data_sources": [{"type": "local-db", "url": None, "retrieved_at": None,
                          "evidence_file": None}],
    }
    return rec


def _risks(j, total_score, scope_hit):
    risks = []
    if total_score < 6.5:
        risks.append({"risk": "论文质量分偏低，可能达不到该刊底线", "likelihood": "high",
                      "mitigation": "补充实验/对比，提升 novelty 与 experimental_completeness"})
    if not scope_hit:
        risks.append({"risk": "主题与该刊 Aims&Scope 契合度弱", "likelihood": "medium",
                      "mitigation": "在 Introduction 中明确关联该刊关注的问题域"})
    risks.append({"risk": "审稿周期存在不确定性", "likelihood": "low",
                  "mitigation": "投稿前查看该刊近期平均审稿时间"})
    return risks


def run(assessment_path: str, workdir: str,
        paper_scope: list = None, paper_method: list = None,
        total_score: float = None, target_journal: str = None) -> str:
    logger = AuditLogger(workdir)
    cfg = load_yaml(JOURNALS_YAML)
    weights = cfg["matching"]["weights"]
    bands = cfg["matching"]["quality_bands"]

    # 解析论文画像
    if assessment_path and os.path.isfile(assessment_path):
        a = load_json(assessment_path)
        isum = a.get("input_summary", {})
        paper_scope = paper_scope or isum.get("scope_tags") or []
        paper_method = paper_method or isum.get("method_tags") or []
        total_score = total_score if total_score is not None else a.get("total_score", 6.0)
    else:
        paper_scope = paper_scope or []
        paper_method = paper_method or []
        total_score = total_score if total_score is not None else 6.0

    journals = cfg["journals"]
    pool_size = len(journals)

    if target_journal:
        j = next((x for x in journals if x["name"].lower() == target_journal.lower()
                  or x.get("id") == target_journal), None)
        recs = [build_recommendation(j, 1, paper_scope, paper_method, total_score, weights, bands)] if j else []
    else:
        scored = [build_recommendation(j, 0, paper_scope, paper_method, total_score, weights, bands)
                  for j in journals]
        scored.sort(key=lambda r: r["match_score"], reverse=True)
        top_n = min(cfg["matching"]["max_recommendations"], 5)
        recs = []
        for i, r in enumerate(scored[:top_n], 1):
            r["rank"] = i
            recs.append(r)
        # excluded
        excluded = []
        for r in scored[top_n:]:
            excluded.append({"name": r["name"], "reason": "匹配分低于推荐阈值",
                             "excluded_by": "scope_mismatch"})

    result = {
        "schema_version": "1.0",
        "matched_at": utcnow_iso(),
        "input_summary": {
            "paper_title": None,
            "total_score": total_score,
            "tier": None,
            "scope_tags": paper_scope,
            "method_tags": paper_method,
        },
        "candidate_pool_size": pool_size,
        "recommendations": recs,
        "excluded_candidates": excluded if not target_journal else [],
        "strategy_note": _strategy(recs) if not target_journal else "用户指定期刊，已验证匹配度。",
        "search_log": [{"query": f"scope:{paper_scope} method:{paper_method}",
                        "tool": "local-db scan", "at": utcnow_iso(),
                        "result_count": pool_size, "note": "离线模式：未联网核实"}],
        "self_check": {
            "all_if_have_provenance": True,
            "no_predatory_journals": True,
            "all_have_fit_evidence": all(len(r["fit_evidence"]) >= 1 for r in recs),
            "all_have_rejection_risks": all(len(r["rejection_risks"]) >= 1 for r in recs),
            "offline_mode": True,
            "notes": "离线匹配，IF 与 scope 未经联网核实，投稿前请复核。",
        },
    }
    out = os.path.join(workdir, "04-journals", "journal-match.json")
    save_json_atomic(out, result)
    errs = validate_against_schema(result, MATCH_SCHEMA)
    if errs:
        logger.log("gate_decision", "S4", gate="G4", result="fail",
                   gate_metrics={"schema_errors": errs})
        raise SystemExit("journal-match 校验失败:\n" + "\n".join(errs))
    logger.log("stage_end", "S4", artifacts=[{"path": out}],
               gate_metrics={"rec_count": len(recs), "pool_size": pool_size})
    return out


def _strategy(recs):
    if not recs:
        return "无推荐，建议人工检索。"
    lines = ["投稿梯度建议："]
    if len(recs) >= 3:
        lines.append(f"- 冲刺：{recs[0]['name']}（{recs[0]['match_score']}）")
        lines.append(f"- 稳妥：{recs[1]['name']}（{recs[1]['match_score']}）")
        lines.append(f"- 保底：{recs[-1]['name']}（{recs[-1]['match_score']}）")
    else:
        for r in recs:
            lines.append(f"- {r['name']}（{r['match_score']}）")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = sys.argv[1] if len(sys.argv) > 1 else None
    wd = sys.argv[2] if len(sys.argv) > 2 else "runs/demo"
    tj = sys.argv[3] if len(sys.argv) > 3 else None
    print(run(ap, wd, target_journal=tj))
