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

### 2.2 可选：目标期刊写作模式蒸馏

期刊匹配回答“研究是否适合该刊”，写作模式蒸馏只回答“同刊同体裁论文通常怎样组织和呈现”。
二者不得合并计分。蒸馏档案属于 `observed_pattern`，不能覆盖 `official_requirement`，也不能作为
录用概率、科学质量或投稿就绪的证据。

仅在作者合法取得全文并明确需要目标期刊适配时执行：

1. 语料限定为同一 ISSN 与 article type；每篇记录 DOI、来源 URL、访问依据、文件 SHA-256、
   `metadata_verified`、`full_text_read` 与 `visual_checked`。
2. 提炼前按作者组划分 `train / heldout`；同一团队或同文不同版本不得跨组。
3. 训练卡只记录自己归纳的结构/修辞定义和页、节、段定位，不保存原句、摘要、摘录、全文、
   论文结论或数字。付费或机构访问只赋予阅读权限时，`redistribution_allowed` 必须如实为 `false`。
4. 相同 `pattern_id` 的定义发生冲突时停止，不静默合并；规则支持度按不同论文和不同作者组统计。
5. 最小训练篇数、作者组数与规则支持组数由项目显式设定。它们是工程取样策略，不是期刊规范，
   也不是“样本充分”的科学证明。
6. 首次编译只能得到 `DRAFT_NEEDS_HELDOUT_EVALUATION`。只有留出作者组评测与人工确认绑定到
   当前 profile fingerprint 后，才能得到 `USABLE_WITH_RECORDED_HUMAN_APPROVAL`。

输入 JSON 的核心结构为：

```json
{
  "schema_version": "1.0",
  "journal": {"name": "Target Journal", "issn": "1234-5679"},
  "article_type": "Research Article",
  "papers": [{
    "id": "paper-a",
    "doi": "10.xxxx/example",
    "source_url": "https://publisher.example/article",
    "access_basis": "open_access",
    "redistribution_allowed": false,
    "file_sha256": "<64 lowercase hex characters>",
    "author_group": "team-a",
    "split": "train",
    "metadata_verified": true,
    "full_text_read": true,
    "visual_checked": true,
    "observations": [{
      "pattern_id": "validation-before-interpretation",
      "dimension": "validation_reporting",
      "definition": "Report the validation result before interpreting its implication.",
      "locator": "p. 4, Results, paragraph 2"
    }]
  }]
}
```

可执行编译器：

```bash
python scripts/readiness/journal_style_profile.py \
  --cards journal-evidence/style-cards.json \
  --min-train-papers <project-minimum> \
  --min-train-author-groups <project-minimum> \
  --min-pattern-author-groups <project-minimum> \
  --out 08-readiness/journal-style-profile.json
```

未提供合格留出评测时命令退出码为 2，这是诚实阻断而不是执行故障。根据首次输出的
`profile_fingerprint` 制作评测 JSON，再用 `--evaluation` 重跑。评测必须覆盖精确的 `heldout_ids`，
并分别确认科学内容、数字/单位/公式、引用、结构效果和无原句模仿；编译器只验证这些声明的结构，
不能证明人工判断本身正确。

修订时只加载通过评测的 profile，不加载源论文语料。它只可影响问题引入、模型说明、验证报告、
结果解释、局限和文章结构；事实、数据、公式、引用、证据强度、模型输出与主张上限继续受
FORGE × TRACE 和变更控制约束。若风格要求与科学完整性冲突，保留科学内容并交作者处理。

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
