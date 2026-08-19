# 期刊数据库说明（journal-database）

> 供 S4 期刊匹配参考。主数据库在 `config/journals.yaml`，本文件说明其结构与扩展方式。

## 1. 数据来源与可信度

- `journals.yaml` 中的影响因子（IF）为 **seed-data UNVERIFIED**（种子数据，未经联网核实）。
- 每次 S4 运行默认离线模式：IF 标注 `local-cache (seed-data UNVERIFIED)`，
  报告必须显著声明"投稿前请自行复核"。
- 联网核实（DOI / JCR / 期刊官网 / Crossref）由 S4 提示词层执行，结果落盘到
  `journal-evidence/<id>-scope.md` 并写入 `data_sources.evidence_file`。

## 2. 期刊条目字段

| 字段 | 用途 |
|------|------|
| `id` | 内部 id，回填到 `journal-match.json#recommendations[].journal_id` |
| `scope_tags` / `method_tags` | 匹配用标签，与论文 `scope_tags`/`method_tags` 求交 |
| `impact_factor` | `{value, year, source, retrieved}`；离线时 value 保留但 source 标 UNVERIFIED |
| `quartile` | JCR 分区 Q1–Q4，参与 `tier_alignment` 评分 |
| `review_weeks` | `[下限, 上限]`，用于 `practical_fit` |
| `open_access` | gold/hybrid/green/closed，影响 APC 与友好度 |
| `template` | `{latex, docx, bundled_fallback}`，S5 取模板用 |
| `constraints` | 投稿硬约束（字数/关键词/参考文献样式等），S5/S6 校验 |
| `predatory_signals` | 若为 null 表示未标记；非空则 S4 排查 |

## 3. 顶层的匹配配置（`matching`）

- `weights`：scope_fit / method_fit / quality_fit / tier_alignment / practical_fit 的权重。
- `quality_bands`：按论文 `total_score` 划分目标分区与策略说明。
- `min/max_recommendations`：推荐数量区间（正常 3–5）。
- `require_gradient`：是否要求冲刺/稳妥/保底的梯度策略。

## 4. 如何扩充数据库

1. 在 `journals.yaml#journals` 追加条目，遵循现有字段结构。
2. 在 `taxonomy.scope_tags` / `method_tags` 注册新标签（若用到新标签）。
3. IF 务必标注 `source: "seed-data JCR≈YYYY (UNVERIFIED)"` 与 `retrieved` 日期。
4. 运行 `pytest tests/test_journals.py` 验证 schema 与评分逻辑未被破坏。
5. 详见 `CONTRIBUTING.md`。

## 5. 反掠夺性（predatory）

- S4 对照 `predatory_signals` 与 Beall's list 类信号。
- 命中即排除，并在 `excluded_candidates` 登记 `excluded_by: predatory_risk`。
- 本仓库不收录已知掠夺性期刊；若社区贡献，须附可信来源。
