# Module W — SCI Paper Writing / 论文撰写

> 路径：`prompts/08-sci-writing.md`
>
> 使用前必须读取：`prompts/shared/05-integrity-preservation.md`。
> 若任务来自数学建模报告转换，本模块是**增量能力**，不得替换原有 S1–S7 的任何保护规则。

## 目标

把已有研究材料组织成结构严谨、证据可追溯、适合 SCI 论文语境的正文。
本模块可以用于：
- 从研究材料/结果/提纲撰写完整论文或单个章节；
- 重构 Introduction / Related Work / Methods / Results / Discussion / Conclusion；
- 建立研究问题—证据—结论的逻辑链；
- 在已有建模稿件完成 S2 后，进一步增强 SCI 论证结构。

本模块**不负责**凭空生成实验、数据或参考文献。

---

## W0. 输入审计：先建立 Source Ledger

写正文前，建立最小来源账本：

```yaml
research_question:
target_article_type:
target_journal: null
source_material:
  - id:
    type: manuscript|figure|table|equation|dataset|code|reference|user_note
    location:
protected_items:
  figures: []
  tables: []
  equations: []
  numerical_claims: []
  core_conclusions: []
  key_arguments: []
missing_evidence: []
terminology_lock: []
symbol_lock: []
```

如果用户只要求写一小段，可以内部完成该审计而不强制展示整个 YAML，但仍必须遵守。

### 来源映射原则

每个定量结论、因果结论、比较结论至少能回指到：
1. 原稿/数据/图表；或
2. 用户确认；或
3. 已核验文献。

若不能回指，使用 `[[MISSING: evidence for ...]]`，不要“合理补全”。

---

## W1. 先锁定 Paper Argument

在写大段正文前，先确定五项：

1. **Research Question**：本文真正回答什么问题？
2. **Gap**：已有研究/方法具体缺什么？Gap 必须可由文献或已知限制支撑。
3. **Approach**：本文用什么数据、模型、实验或推导回答？
4. **Evidence**：哪些图、表、公式、统计量直接支撑主要发现？
5. **Contribution**：与现有工作相比新增了什么可验证内容？

将贡献写成“可审稿”的陈述，而不是宣传语。优先：
- 新数据/新事件/新尺度；
- 新模型/算法/理论推导；
- 新比较、系统性验证；
- 新的可复现数据产品/方法；
- 对已有机制/理论的限定、扩展或反例。

避免把“首次”“突破性”“state-of-the-art”当作默认贡献，除非已通过文献检索核实。

---

## W2. 结构设计

若目标期刊已有官方结构，服从官方结构。否则使用可解释的 IMRaD 变体。

### Abstract

推荐信息顺序：
1. 研究背景/问题（必要时 1–2 句）；
2. 明确研究缺口或目标；
3. 数据/方法；
4. 最关键的定量结果；
5. 主要结论与边界；
6. 研究意义（不能超过证据强度）。

规则：
- 不引入正文没有的新结果；
- 数字、单位、符号与正文一致；
- 不用空泛“important/significant/crucial”替代量化结果；
- 机制若为解释而非直接观测，必须用避险表达。

### Introduction

建议的逻辑链：

```text
已知背景
  → 已有研究已经解决什么
  → 仍未解决的具体问题/不一致
  → 为什么这个缺口值得解决
  → 本文用什么数据/方法处理
  → 本文回答什么问题、贡献是什么
```

每段首句承接前文“旧信息”，段尾放本段最需要推进的“新信息”。
不要用按作者逐篇罗列的文献综述替代逻辑综合。

### Related Work / Literature Review

按**科学问题、方法、假设、数据类型或结论差异**组织，而不是：
“Author A did X. Author B did Y. Author C did Z.”

每个主题单元至少回答：
- 各研究在哪个问题上可比？
- 方法/样本/尺度有何差异？
- 结论一致还是冲突？
- 这些差异如何导向本文问题？

新增参考文献必须先验证 DOI 或权威来源；无法验证时标记 `[[UNVERIFIED_REF]]`，不得进入最终参考文献。

### Methods

以可复现为目标，依次检查：
- 数据/样本来源、时间与空间范围；
- 纳入/排除规则；
- 预处理；
- 模型假设；
- 方程、变量定义、单位；
- 算法/软件/版本；
- 参数与超参数；
- 统计检验和不确定度；
- 复现实验所需的随机种子/硬件（若相关）；
- 伦理/数据许可（若相关）。

数学建模原稿中的公式、约束、变量语义不得为了“写得更像论文”而重写。

### Results

推荐基本单元：

```text
Claim → Evidence → Quantification → Boundary
```

例如：
- 先说观察到什么；
- 再给图表/数值；
- 再给幅度、范围、不确定度或统计量；
- 最后说明该结果在哪些条件下成立。

Results 主要回答“发生了什么”，不要把缺乏证据的机制讨论提前写成结果。

### Discussion

推荐基本单元：

```text
Observed result
  → Interpretation
  → Plausible mechanism (hedged if indirect)
  → Comparison with prior work
  → Alternative explanation / uncertainty
  → Implication
```

若缺乏直接测量（例如风场、能量沉积、电导率、某个中间过程），
机制必须写成“consistent with / suggests / may reflect”，并明确说明证据边界。

### Conclusion

只做三件事：
1. 回答 Research Question；
2. 总结最有支撑的结果；
3. 给出清晰限制与下一步。

不得在结论中新增正文没有展示的数据、机制或引用。

---

## W3. 段落与句子工程

每个段落至少执行以下检查：

- **Purpose**：本段承担什么功能？
- **Topic**：首句是否给读者定位？
- **Evidence**：关键句有无数据/引用/逻辑支撑？
- **Warrant**：证据为什么支持该结论？
- **Transition**：末句是否为下一段提供自然接口？

优先使用主动、物理/数学意义明确的动词，例如：
`increased`, `decreased`, `constrained`, `redistributed`, `advected`,
`amplified`, `suppressed`, `converged`, `diverged`, `estimated`, `resolved`。
避免无信息量的名词化结构和套话。

句式不追求机械统一。长句用于限定条件与因果链，短句用于关键结果和转折。

---

## W4. 文献检索与 Gap 校验

当论文撰写需要外部文献时，按三轮检索：

1. **Direct**：核心主题 + 方法 + 对象；
2. **Adjacent**：同一问题的相邻方法/相邻学科；
3. **Foundational / Citation trail**：关键综述、经典方法和被高频引用工作。

最低要求：
- 优先近期原始研究 + 必要经典文献；
- 记录 DOI/出版信息；
- 不因某条搜索结果“看起来像”就视为存在；
- Gap 必须在检索后校准，不允许先写“few studies have...”再找证据凑。

---

## W5. Reviewer-Perspective Self Check

完成章节或全文后，用 5 个维度自检，每项 0–20：

| 维度 | 核心问题 |
|---|---|
| Argument | 问题、gap、方法、证据、结论是否闭环？ |
| Evidence | 定量/文献/机制性陈述是否有来源？ |
| Reproducibility | 方法是否足以复现，公式/参数/数据范围是否清楚？ |
| Coherence | 段落是否按旧→新信息推进，跨章节术语是否一致？ |
| Venue Fit | 结构、字数、文章类型是否符合已核验的目标期刊要求？ |

低于 80/100 不意味着“不能输出”，但必须指出最弱项及可执行修订。
任何 `MISSING`、`UNVERIFIED_REF` 或保护内容冲突，单独列为阻塞项，不可被总分掩盖。

---

## W6. 输出契约

根据任务规模输出：
- 完整正文/章节；
- `Source & Evidence Notes`（列出新增外部事实和缺口）；
- `Protected Content Check`（确认图/表/公式/核心结论/关键论述是否保持）；
- `Revision Risks`（如机制证据不足、文献 Gap 尚未完全验证等）。

若用户只要“直接给正文”，正文优先；审计信息可以压缩到正文后 3–6 条。
