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
