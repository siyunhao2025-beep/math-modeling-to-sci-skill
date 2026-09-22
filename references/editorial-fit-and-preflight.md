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
- 模板来源和编译结果已验证；
- 匿名、作者信息、利益冲突、基金、伦理、知情同意、数据/代码可用性与 AI 披露按需存在；
- 图表格式、分辨率、色彩和版权符合指南；
- 审稿模拟重大问题已关闭；
- 上传或发送动作已获得用户授权。

输出只使用 `BLOCKED`、`AUTHOR_ACTION_REQUIRED` 或 `READY_FOR_HUMAN_SUBMISSION_CHECK`。最后一项仍需作者/导师人工复核。
