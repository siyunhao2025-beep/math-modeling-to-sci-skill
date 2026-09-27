# 期刊匹配、模拟审稿与投稿前检查

## 1. 建立 manuscript profile

至少记录：研究问题、对象与场景、文章类型、核心方法、证据类型、样本/数据规模、主要贡献、主张上限、篇幅、图表数量、数据代码状态、伦理与披露需求。

## 2. 候选期刊证据卡

每个候选必须有：

- 官方期刊名称、ISSN 与出版社；
- 官方 Aims & Scope URL 与检索日期；
- 官方 article type 与 Guide for Authors URL；
- 近期同类论文的标题/DOI/日期与相似点；
- 当前模板、字数/图表/补充材料要求；
- 数据、代码、AI、伦理、预印本和匿名政策；
- IF、分区、APC、审稿周期等时效项的来源、年份和日期；
- scope、method、evidence、audience、format、practical 六类契合判断；
- desk-reject 风险、证据缺口和作者成本。

本地期刊库只能生成候选，不得作为当前指标和规则的最终来源。

### 2.1 身份、来源类别与刷新状态

先解析期刊身份，再做匹配。优先键为校验通过的 ISSN/eISSN；若刊名相同、期刊更名、
印刷版/电子版映射或出版社归属仍有歧义，状态为 `UNRESOLVED`，不得静默合并候选。

把证据分成两类：

- `official_requirement`：当前 Aims & Scope、article type、作者指南、模板、费用、
  收录状态、投稿入口和披露政策；
- `observed_pattern`：近期已发表论文呈现出的主题、方法、篇幅和版式惯例。

后者能补充软匹配，不能替代前者通过硬过滤。每份官方证据记录 URL、带时区的
`checked_at` 与项目显式设置的 `max_evidence_age_days`，再标为
`CURRENT / STALE / UNVERIFIED`。刷新天数只是工作流的保守操作阈值，不是关于期刊政策
稳定性的科学断言；超过阈值、缺时间、无时区或未来时间均阻断投稿就绪结论。

可执行基线：

```bash
python scripts/readiness/journal_fit.py \
  --manuscript manuscript.md --journal-name "Target Journal" --issn 1234-5679 \
  --aims-scope-file journal-evidence/scope.txt --scope-source-url https://publisher.example/scope \
  --article-types-file journal-evidence/article-types.txt --article-type "Research Article" \
  --article-type-source-url https://publisher.example/guide \
  --evidence-checked-at 2026-09-28T09:00:00+08:00 --max-evidence-age-days 30 \
  --out journal-evidence/fit.json
```

示例中的 30 天不是通用建议；每个项目应依据投稿临近程度和规则变动风险自行设定。

## 3. 推荐方式

给 3–5 个有梯度候选：

- **reach**：影响力更高，但贡献或验证要求更高；
- **fit**：范围与证据最匹配；
- **safe**：范围较稳，但仍需满足质量底线。

梯度不等于录用概率。不要用“保底必中”“成功率 X%”。对每个候选明确推荐理由与不推荐理由。

## 4. 多角色模拟审稿

使用 3–5 个独立角色：

- handling editor：范围、体裁、贡献门槛；
- domain reviewer：问题、文献与替代解释；
- methods/statistics reviewer：设计、基线、不确定性和复现；
- skeptical reviewer：反例、过度声称和失败模式；
- reproducibility reviewer：数据、代码、环境和图表重建。

不把角色分数平均。先按以下顺序裁决：

1. 评审未完成 → `INCOMPLETE`；
2. 有未关闭 blocker → `BLOCKED`；
3. 科学类意见不足 → `INSUFFICIENT_SCIENTIFIC_COVERAGE`；
4. 角色结论显著分歧 → `PANEL_DISAGREEMENT`；
5. 无 blocker 且均可进入人工复核 → `READY_FOR_HUMAN_SUBMISSION_CHECK`；
6. 其他 → `REVISION_REQUIRED`。

## 5. Preflight

至少检查：

- 稿件、补充材料、图表、cover letter 和声明版本一致；
- 题名、摘要、正文、图表和结论数字一致；
- 引用身份与句子支持无 blocker；
- 目标期刊和 article type 已由官方来源确认；
- 期刊身份已解析，影响硬过滤的官方事实处于 `CURRENT`，且未以近期论文样本替代官方规则；
- 模板来源和编译结果已验证；
- 匿名、作者信息、利益冲突、基金、伦理、知情同意、数据/代码可用性与 AI 披露按需存在；
- 图表格式、分辨率、色彩和版权符合指南；
- 审稿模拟重大问题已关闭；
- 上传或发送动作已获得用户授权。

输出只使用 `BLOCKED`、`AUTHOR_ACTION_REQUIRED` 或 `READY_FOR_HUMAN_SUBMISSION_CHECK`。最后一项仍需作者/导师人工复核。
