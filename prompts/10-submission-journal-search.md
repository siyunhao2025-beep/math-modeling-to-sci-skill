# Module J — Journal Search, Submission & Formatting / 期刊检索与投稿

> 路径：`prompts/10-submission-journal-search.md`
>
> 使用前必须读取：`prompts/shared/05-integrity-preservation.md`。
> 对数学建模报告的期刊匹配，原有 S4/S5/S6 仍是主流程；本模块为其增加更细的实时核验与投稿闭环。

## 目标

完成从“这篇文章适合投哪里”到“按目标期刊要求准备可投稿材料”的可追溯流程，覆盖：
- 期刊候选发现与匹配；
- 当前 Aims & Scope / article type 核验；
- IF/分区/APC/收录/模板等时效数据核验；
- 投稿格式规范矩阵；
- Cover Letter 与必要声明；
- 投稿前 preflight；
- 拒稿后的转投策略；
- 审稿意见 point-by-point 回复。

**不预测录用，不保证审稿周期，不为迎合期刊修改科学结果。**

---

## J0. Manuscript Profile

从标题、摘要、关键词、方法和主要结果提取：

```yaml
topic:
research_question:
article_type:
methods:
data_or_sample:
main_results:
evidence_strength:
audience:
novelty_claims:
constraints:
  oa_required:
  apc_budget:
  desired_indexing:
  desired_quartile:
  time_constraint:
  publisher_exclusions:
  region_preferences:
```

缺失的信息允许为空。不要为了完成表格臆造“样本量”“创新等级”或“期望 IF”。

---

## J1. 候选期刊发现

### 1. 候选池

可以组合：
- `config/journals.yaml`（仅作种子池，时效字段必须重新验证）；
- 论文参考文献中高频出现的期刊；
- 相似主题近期论文的发表期刊；
- 出版社/学会官方 Journal Finder；
- 权威数据库的学科/主题检索。

### 2. 硬过滤

以下任一项明显不符时应降权或剔除：
- Aims & Scope 不覆盖核心主题；
- 不接受该 article type / study design；
- 方法或数据类型明显不在期刊常见范围；
- 当前收录状态不满足用户要求；
- 用户明确排除该出版社/付费模式；
- 已知存在需要核验的停刊/剔除/更名问题。

不要因为 IF 高就保留 scope 明显不匹配的期刊。

---

## J2. 实时证据卡（每个候选都要有）

每个候选至少记录：

| 字段 | 要求 |
|---|---|
| Journal | 正式刊名 |
| Publisher / Society | 当前出版方 |
| Official URL | 官方主页 |
| Aims & Scope | 与稿件相关的范围证据 |
| Article Type | 是否接受本稿类型 |
| Indexing | 用户关心的数据库，注明核验来源 |
| Metric | IF/CiteScore/SJR，注明指标、年份、来源 |
| Quartile | 明确是 JCR/SJR/中科院等哪套体系 + 年份 |
| OA / APC | gold/hybrid/subscription，金额与币种若有 |
| Format | 字数、摘要、关键词、图表、参考文献、补充材料 |
| Template | Word/LaTeX 官方模板 |
| Submission system | 当前投稿入口 |
| Review-time claim | 只有可核验时提供，并标明来源类型 |
| Retrieved | 核验日期 |

### 来源优先级

1. 期刊/出版社官方页面；
2. Clarivate Master Journal List / JCR、Scopus、DOAJ、ISSN Portal；
3. Crossref 等元数据来源；
4. 可靠第三方统计。

如果两个来源冲突，以官方当前规则为主，并把冲突写入 `journal-evidence/`。

---

## J3. 匹配评分（100 分）

默认评分：

- **Scope fit — 30**：研究问题与 Aims & Scope 的直接重合度；
- **Method/data fit — 15**：该刊是否经常接收相似方法/数据类型；
- **Contribution/evidence fit — 15**：论文证据成熟度与期刊定位是否匹配；
- **Audience fit — 10**：目标读者是否真正需要该工作；
- **Article-type & format fit — 10**：稿件类型和篇幅是否匹配；
- **Practical fit — 10**：OA/APC/时效/作者约束；
- **Indexing/reputation fit — 10**：是否满足用户的收录/分区目标。

不要把“高影响因子”单独等同于“高匹配”。

### 推荐梯度

最终给 3–5 个候选，并可分：
- **Ambitious**：范围高度匹配但门槛较高；
- **Balanced**：范围、方法与证据成熟度最均衡；
- **Conservative**：更稳妥但仍必须 scope 合理。

这些标签只表示投稿策略，不是录用概率。

---

## J4. 推荐表的最低字段

```text
Journal | Strategy tier | Fit score | Scope evidence | Method fit |
Current verified metrics | OA/APC | Key format constraints |
Main rejection risk | Required manuscript changes | Confidence
```

对每个期刊写清：
- 为什么匹配；
- 为什么可能不匹配；
- 哪些信息是实时核验；
- 哪些信息仍未知。

给出一个**首选**，但不宣称“最容易录用”。

---

## J5. 确定目标期刊后的 Submission Compliance Matrix

锁定一个目标期刊后，重新读取官方 Author Guidelines，生成矩阵：

```yaml
manuscript_type:
word_limit:
abstract_limit:
keywords:
heading_structure:
figure_limits:
table_limits:
figure_resolution:
reference_style:
supplementary_policy:
data_availability:
code_availability:
ethics:
funding:
conflict_of_interest:
author_contributions:
ai_disclosure:
cover_letter:
highlights:
graphical_abstract:
suggested_reviewers:
blinded_review:
file_naming:
submission_portal:
```

每项状态：
- `PASS`
- `FIX`
- `NOT_REQUIRED`
- `UNKNOWN_NEEDS_VERIFICATION`

任何 `UNKNOWN` 不得伪装成满足要求。

### 数学建模稿件冲突处理

如果期刊限制要求减少图/表/公式，而这些对象属于保护内容：
- 先标 `[[JOURNAL_CONFLICT]]`；
- 推荐更换版式、补充材料或更换期刊；
- 未经作者明确同意，不执行删除/压缩。

---

## J6. 投稿材料包

### 主稿
- 目标期刊官方模板；
- 标题页/匿名稿按双盲要求区分；
- 图表、补充材料、参考文献完整；
- 所有 cross-reference 可解析。

### Cover Letter

只写可核实内容，建议顺序：
1. 稿件标题与 article type；
2. 一句话说明研究问题；
3. 2–3 句概括方法与最有力结果；
4. 为什么与该刊 Aims & Scope 匹配；
5. 研究贡献，不夸大；
6. 原创性/未一稿多投声明——**只有用户或真实投稿状态已确认时才能写**；
7. 伦理、利益冲突、数据/代码、AI 使用等期刊要求的声明；
8. 礼貌结束。

不要写“this groundbreaking work will definitely attract broad readership”之类空泛营销。

### 其他材料
仅在期刊要求时生成：
- Highlights；
- Graphical Abstract；
- Lay/Plain Language Summary；
- CRediT author contributions；
- Data/Code Availability；
- Funding / COI / Ethics；
- AI-assisted writing disclosure；
- Suggested reviewers。

推荐审稿人时必须检查明显利益冲突；不要虚构邮箱或单位。

---

## J7. Pre-submission Preflight

至少检查：

### 科学内容
- Research Question、Methods、Results、Conclusion 对齐；
- 所有数字/单位/公式/图表引用一致；
- `[[MISSING]]`、`[[UNVERIFIED_REF]]` 清零或明确阻塞；
- 机制表述不超过证据。

### 期刊规范
- article type；
- 字数；
- 摘要；
- 关键词；
- 图表；
- 引用格式；
- 文件类型；
- 匿名要求；
- 声明；
- Cover Letter；
- 投稿入口。

### 完整性
- 数学建模保护项没有被删除、压缩或重写；
- 任何格式适配只改变 presentation，不改变 science。

---

## J8. 拒稿后的转投

收到 desk reject / reject 后：
1. 区分 scope rejection、novelty/evidence rejection、format rejection、reviewer scientific criticism；
2. 不在没有证据的情况下“迎合”上一家审稿意见；
3. 更新 manuscript profile；
4. 重新筛选 3–5 个候选；
5. 若不再投原模板，先恢复中性稿，再适配新刊，避免残留旧期刊格式。

---

## J9. 审稿意见回复

每条评论建立稳定 ID：`R1-1`, `R1-2`, `R2-1`...

推荐结构：

```text
Reviewer Comment
Response
Change Made
Location
```

规则：
- 完整回答，不跳过不喜欢的评论；
- 如果同意：说明做了什么并给准确位置；
- 如果部分同意：区分同意与保留部分；
- 如果不同意：礼貌、基于数据/文献解释，并说明是否为提高可读性做了澄清；
- 不虚构“已补实验/已修改”；
- 页码/行号不确定时使用 section + paragraph 标识，不猜页码；
- 重大科学修改必须同步更新摘要、结果、讨论、结论等相关位置。

---

## J10. 输出契约

### 期刊检索阶段
输出：
1. Manuscript profile；
2. 3–5 个期刊比较；
3. 首选 + 备选顺序；
4. 每个候选的证据来源与核验日期；
5. 不确定项与风险。

### 投稿准备阶段
输出：
1. Compliance matrix；
2. 待修改清单；
3. 投稿材料包；
4. Preflight 结果；
5. `journal-evidence/` 所需存证清单。

### 审稿回复阶段
输出：
1. Editor overview；
2. point-by-point response；
3. 修改位置；
4. 未解决/需作者确认项目。
