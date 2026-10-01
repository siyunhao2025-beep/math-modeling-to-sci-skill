# Module P — Academic Language Polishing / 学术语言润色

> 路径：`prompts/09-language-polish.md`
>
> 使用前必须读取：`prompts/shared/05-integrity-preservation.md`。

## 目标

提高语法、句法、可读性、学术语体、段落连贯性和术语一致性，同时**冻结科学事实**。
本模块的基本原则是：

> **Polish the prose, not the science.**

对于数学建模稿件，图片、表格、公式、核心结论和关键论述受强制保护，默认不能因“更简洁”
“更像 SCI”或“更自然”而被删除、压缩或重写其科学含义。

---

## P0. 先选润色级别

### Level 1 — Proofread
适合“语法检查/英文纠错”：
- 拼写；
- 冠词；
- 主谓一致；
- 时态；
- 标点；
- 明显病句。

不改变段落结构和论证顺序。

### Level 2 — Academic Polish（默认“润色”模式）
在 Level 1 基础上：
- 改善句式；
- 消除冗余；
- 优化 topic–stress；
- 统一学术语气；
- 调整连接方式；
- 统一术语和时态。

不新增科学机制，不改变结论强度。

### Level 3 — Structural Polish
只有用户明确要求“深度润色/重构逻辑/按顶刊风格重写”时启用：
- 可调整段落顺序；
- 可重构论证连接；
- 可提出需要移动/拆分的句子。

但任何涉及保护科学内容的“删减、合并、重写”都必须先得到用户授权。
未获授权时，只给建议，不执行。

---

## P1. Protected Span Lock

开始润色前锁定：

```text
LaTeX commands/environments
equations and inline math
citation commands and citation keys
figure/table/equation labels
DOI/URL
dataset/instrument/software names
all numeric values and signs
units
uncertainty / CI / p-values
user-defined terminology
core conclusions
key scientific arguments
```

### LaTeX 特别规则

- 不改 `\section`, `\subsection`, `\cite`, `\ref`, `\label`, `\begin`, `\end` 等命令；
- 不改数学环境内部内容；
- 不把 `~`, `\,`, `\pm`, `%` 等具有排版/数学语义的符号随意替换；
- 长项目按**章节/段落边界**切分，不在公式、命令参数或一句话中间切分；
- 每个片段处理后按原序合并，并对比原文件；
- 原始文件保留，润色版本作为新版本输出。

这是一个工作流原则，不依赖任何特定外部项目实现。

---

## P2. Scientific Meaning Freeze

逐句润色前先识别该句属于哪一类：

1. **Observation / Result**：直接来自数据、图、表、计算；
2. **Method**：实际执行的处理与模型；
3. **Established knowledge**：有文献支持的事实；
4. **Interpretation**：对结果的解释；
5. **Mechanism hypothesis**：间接推断；
6. **Limitation / uncertainty**。

润色后的句子必须保持同一类别。尤其禁止：

- 把 `may suggest` 改成 `demonstrates`；
- 把相关性写成因果；
- 把“模型结果”写成“观测事实”；
- 把“一个事件/一个数据集”泛化成普遍规律；
- 把“不显著/不确定”改成“明显/显著”；
- 为了语言更有力而扩大空间、时间或样本范围。

---

## P3. Academic Modality Calibration

### 直接观测
可以使用较明确动词：
`showed`, `increased`, `decreased`, `reached`, `remained`, `extended`.

### 间接机制
优先：
`suggests`, `implies`, `is consistent with`, `may reflect`,
`points to a potential role of`, `cannot be ruled out`, `is likely associated with`.

### 避免绝对化
除非有严格证明，否则避免：
`definitely`, `completely proves`, `perfectly`, `flawless`,
`undoubtedly`, `unambiguously`。

### 避免“AI 味”套话
删除或重写不承载科学信息的表达，例如：
- `It is worth noting that ...`
- `It should be emphasized that ...`
- `plays a crucial/pivotal/essential role`
- `provides valuable insights into ...`
- `a comprehensive understanding of ...`
- `in today's rapidly evolving ...`

不是机械禁词：如果上下文确实需要“note/emphasize”，可以保留，但必须有具体对象和理由。

---

## P4. Strong Verbs & De-nominalization

把空洞名词化替换为具体动作，前提是不改变科学含义：

- `conducted an evaluation of` → `evaluated`
- `showed an increase in` → `increased`
- `performed an analysis of` → `analyzed`
- `resulted in a suppression of` → `suppressed`（只有因果证据允许时）
- `was responsible for` → 谨慎改为 `likely drove / was associated with`，取决于证据等级

动词必须描述真实过程，不为追求“强劲”而制造因果。

---

## P5. Topic–Stress 与旧→新信息

段落内遵循：
- 已知/承接信息放句首；
- 新结果、关键数字、需要强调的物理量放句末；
- 下一句用 `This warming...`, `These perturbations...`, `Such a gradient...`
  等明确指代锁住上文；
- 不用连续五六句相同主谓宾节奏；
- 转折词只在逻辑需要时使用，不机械句首 `However/Moreover/Furthermore`。

---

## P5.0. 读者理解与自然翻译契约

清楚不是把论文改成口语，也不是把技术细节删掉。按以下顺序修订：

1. 除标题、表头、图例和代码标签外，正文使用**完整句子**；不能留下只有修饰语、没有谓语或不知道谁做了什么的残句。
2. 优先写清**主体—动作—对象**，并补齐读者判断结论所需的**比较对象**、**适用条件**和明确指代。原稿没有的关系只能标 `[[AUTHOR_CHECK]]`，不能为了顺口补造。
3. 直接说明逻辑或机制关系。比喻、自造压缩说法和模糊代号若会遮住因果链、计算步骤或边界条件，就改成可核查的实体、操作和关系。
4. 翻译按上下文含义和学科公认用法选词，不做**逐词直译**。数据集、仪器、软件、模型、变量与作者定义名称仍受 Protected Span Lock 约束。
5. 不造**自造缩写**或只有当前段落才懂的简称；确需缩写时，首次给出规范全称并保持全文一致。
6. 删除不承载对象、动作或证据的空洞大词；不用另一组同样空洞的词替换。
7. 精简时保留读者复核结论所需的**必要的中间步骤**。先保证信息完整和论证连续，只能在**信息充分之后再精简**重复内容。
8. 面向作者的中文解释可以先说通俗含义再给术语；SCI 正文仍遵守**目标期刊或学科语体**。通俗化不得替换已锁定的专业术语，也不得覆盖期刊对语态、篇幅、定义或格式的硬要求。

本节解决理解成本，不提供新的科学内容。若“更好懂”与事实锁、主张上限、专业术语或期刊规范冲突，放弃该项语言收益。

---

## P5.1. 贡献前置、证据有界的防御性措辞审计

这一步只处理修辞性自我削弱、假想审稿人答辩、重复免责声明和工作日志式叙述，
不是删除负结果、真实限制或竞争解释的许可证。先写一张最小编辑契约：

- **核心贡献**：当前证据能够支持的一句话贡献；
- **主张上限**：不得通过换动词、换指标、换比较口径或扩大范围越过的最强表述；
- **必须保留的边界**：范围条件、来源状态、方法限制、竞争解释、矛盾与负结果；
- **编辑权限**：允许改哪些段落、哪些内容只可建议、哪些含义必须询问作者。

逐条登记疑似防御性表达，不按关键词自动删文。处置只能使用：
`KEEP / TIGHTEN / REFRAME / RELOCATE / CUT / QUERY`。

- `KEEP`：删后会扩大主张、掩盖证据状态，或丢失影响解释的限制、竞争解释、矛盾或负结果；
- `TIGHTEN`：保留同一命题与边界，只去掉重复、自我贬低或无信息量的铺垫；
- `REFRAME`：把工作日志或假想答辩改成“问题—证据—范围”，不得重选指标来隐藏不利结果；
- `RELOCATE`：把必要边界移到其限定的推断附近，移动后仍须保持引用与命题绑定；
- `CUT`：只能删除纯修辞冗余，不得删除事实命题、引用功能、来源状态、范围、方法限制或替代解释；
- `QUERY`：改动可能影响含义、论证层级或作者立场时停止自动修改。

每个已改句必须通过回归检查：新主张不强于原句；观测、报告、解释和因果状态不变；
引用/引语仍支持同一命题；数字、单位、公式、引用键和保护 span 不变。原稿中的负结果、
非显著结果或竞争解释只要影响有效性或解释，就必须保留并准确定位。不能用“删得更多”或
触发词数量下降证明质量提高。

整稿模式输出审计表：`location | function | disposition | reason | preserved boundary | author query`。
局部润色可缩短该表，但内部仍须完成同样的判定与回归。

---

## P6. Precision Audit

润色完成后逐项比对原文与新文：

- 所有数字是否一一对应；
- 正负号是否改变；
- `>` / `<` / `~` / `±` 是否改变；
- 单位是否改变；
- 时间/日期/高度/纬度/经度范围是否改变；
- 样本量是否改变；
- 图表引用是否错位；
- 公式编号是否改变；
- 缩写首次定义是否仍正确；
- 时态是否与章节功能一致；
- “significant” 是否真的表示统计显著；若只是“大”，改成定量描述。

任何差异无法从纯语言编辑解释时，必须标为 `[[AUTHOR_CHECK]]`。

---

## P7. 全文/LaTeX 项目的处理策略

对长文档使用“保护—切分—润色—重组—差异审计”：

```text
1. Freeze protected spans
2. Split at safe structural boundaries
3. Polish each chunk with local context + terminology lock
4. Reassemble in original order
5. Run numerical/symbol/citation consistency checks
6. Produce diff/change log
7. Restore or flag any protected-span mutation
```

不要因为上下文窗口限制而丢弃段落、注释所依赖的结构、图片/表格引用或公式。

---

## P8. 输出契约

默认输出：
1. **Polished text**
2. **Key changes**：只列最重要的语言/逻辑改动
3. **Scientific integrity check**：
   - protected values changed: 0 / list
   - scientific claim strength changed: 0 / list
   - author checks needed: list

如果用户要求“只给润色后的段落”，只输出段落，但内部仍需完成完整性检查。
