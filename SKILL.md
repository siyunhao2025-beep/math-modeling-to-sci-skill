---
name: math-modeling-to-sci
description: 将数学建模结果文章（Word .docx 或 LaTeX .tex）转换为可投稿的 SCI 期刊论文。覆盖输入解析、学术化改写、质量评估打分、SCI 期刊匹配推荐、目标期刊模板适配、多轮格式与引用校验、最终成稿与转换报告输出。当用户提供数学建模报告、竞赛论文（如 MCM/ICM、全国大学生数学建模竞赛）、技术建模文档，并希望改写为学术论文、投稿 SCI、匹配期刊或套用期刊模板时使用本技能。
license: MIT
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# Math Modeling → SCI Paper

把一篇「数学建模报告」变成一篇「可投稿的 SCI 论文」，并附带质量评分、期刊推荐与可追溯的转换报告。

## 什么时候用这个技能

- 用户上传 `.docx` / `.tex` / `.zip`（LaTeX 工程）格式的建模报告，希望改成期刊论文
- 用户问「这篇建模文章能投什么 SCI 期刊」
- 用户需要把已有论文套用某个期刊的 LaTeX/Word 模板
- 用户需要对论文做学术质量评估与改进建议

**不适用**：纯文献综述撰写、从零开始的研究选题、非建模类论文的润色（可以用，但收益有限）。

## 核心设计原则（务必遵守）

1. **不臆造事实**。原文没有的数据、实验结果、数值不得凭空生成。缺失内容一律标记为
   `[[MISSING: 说明]]` 并写入 `gaps` 列表交由作者补充，绝不用编造内容填空。
2. **文献引用必须可验证**。所有新增参考文献必须通过 `WebSearch` / `WebFetch` 检索到真实
   DOI 或权威来源；无法验证的引用标记为 `[[UNVERIFIED_REF]]`，不得写入最终 `.bib`。
3. **数学内容零改动语义**。公式、符号、定义、定理只允许改排版（如 `$..$` → `\begin{equation}`），
   不允许改变数学含义。变量重命名必须全文一致并记录进 `symbol_map`。
4. **阶段间只通过结构化文件传递**。每阶段读取上游 JSON、写出自己的 JSON，
   不依赖对话上下文记忆，保证可断点续跑。
5. **质量门控不通过就不往下走**。见 `config/quality-gates.yaml`。

## 七阶段工作流

```
S1 解析 → S2 学术化改写 → S3 质量评估 → S4 期刊匹配
                              ↓ (gate)
   S7 汇报 ← S6 多轮校验 ← S5 模板适配
```

| 阶段 | 提示词 | 输入 | 输出 |
|------|--------|------|------|
| S1 输入解析 | `prompts/01-ingest-parse.md` | `.docx`/`.tex`/`.zip` | `manuscript.ir.json` |
| S2 学术化改写 | `prompts/02-academic-rewrite.md` | `manuscript.ir.json` | `manuscript.rewritten.json` + `references.bib` |
| S3 质量评估 | `prompts/03-quality-assessment.md` | `manuscript.rewritten.json` | `assessment.json` |
| S4 期刊匹配 | `prompts/04-journal-matching.md` | `assessment.json` + IR | `journal-match.json` |
| S5 模板适配 | `prompts/05-template-adaptation.md` | 上述全部 + 期刊模板 | `build/main.tex` 或 `build/main.docx` |
| S6 多轮校验 | `prompts/06-multi-round-validation.md` | `build/` 产物 | `validation.json`（迭代直至 PASS） |
| S7 结果汇报 | `prompts/07-final-report.md` | 全部工件 | `conversion-report.md` + 成稿 |

编排规则见 `prompts/00-orchestrator.md`，这是**入口提示词**，先读它。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 端到端跑一遍（自动模式）
python scripts/run_pipeline.py \
    --input examples/input/sample-model-report.tex \
    --workdir runs/demo \
    --mode auto

# 只跑某个阶段（断点续跑）
python scripts/run_pipeline.py --workdir runs/demo --stage S3

# 查看某次运行的审计轨迹
python scripts/run_pipeline.py --workdir runs/demo --show-audit
```

`--mode` 取值：
- `auto`：全自动，遇到 gate 失败按 `config/quality-gates.yaml` 的策略自动重试/降级
- `interactive`：每个 gate 处暂停，等作者确认（推荐首次使用）
- `dry-run`：只跑校验与打分，不生成成稿

## 工作目录布局

一次运行的所有产物都在 `--workdir` 下，可完整复现：

```
runs/demo/
├── 00-input/            # 输入文件快照（只读备份）
├── 01-parse/            manuscript.ir.json, parse-warnings.json
├── 02-rewrite/          manuscript.rewritten.json, references.bib, rewrite-diff.md
├── 03-assess/           assessment.json
├── 04-journals/         journal-match.json, journal-evidence/
├── 05-template/         template/, build/main.tex, build/main.docx
├── 06-validate/         validation-round-1.json ... validation-final.json
├── 07-report/           conversion-report.md, manuscript-final.pdf
└── audit.jsonl          全链路审计日志（append-only）
```

## 分阶段执行指引

### S1 输入解析

先判定格式，再调对应解析器：

```bash
python scripts/ingest/detect_format.py --input <file>          # → docx | latex | latex-project | unknown
python scripts/ingest/parse_docx.py  --input <f> --out 01-parse/manuscript.ir.json
python scripts/ingest/parse_latex.py --input <f> --out 01-parse/manuscript.ir.json
python scripts/validate/validate_ir.py --ir 01-parse/manuscript.ir.json
```

解析器做的是**机械抽取**（章节树、公式、图表、引用、元数据）。语义判断（哪段是"研究动机"、
哪段属于"方法"）由 `prompts/01-ingest-parse.md` 指导模型完成后回填 IR 的 `semantic_role` 字段。

### S2 学术化改写

按 `prompts/02-academic-rewrite.md` 执行。核心是三件事：
1. **体裁转换**：竞赛报告体 → 期刊论文体（见 `references/math-modeling-to-paper-mapping.md` 的章节映射表）
2. **补充学术骨架**：研究缺口（research gap）、文献综述、创新点声明、局限性与未来工作
3. **语言规范化**：应用 `config/style-rules.yaml`（时态、语态、第一人称、模糊限定词、禁用词）

新增文献必须走检索验证，写入 `references.bib` 前用 `scripts/validate/check_citations.py --verify-doi` 过一遍。

### S3 质量评估

按 `prompts/03-quality-assessment.md` 的六维度评分卡（创新性、方法论严谨性、实验完整性、
学术表达、结构规范性、可复现性），每维 0–10 分并给加权总分。输出必须符合
`config/schema/assessment.schema.json`。

**Gate G3**：总分 < 阈值时不进入期刊匹配，先回 S2 按 `improvement_actions` 重写。

### S4 期刊匹配

```bash
python scripts/journals/match_journals.py \
    --assessment 03-assess/assessment.json \
    --ir 02-rewrite/manuscript.rewritten.json \
    --out 04-journals/journal-match.json
```

本地期刊库 `config/journals.yaml` 给出候选池与打分基线，**影响因子等时效数据必须用
`WebSearch` 现场核实**（库里的值仅作 fallback，且必须在报告中标注数据年份与来源）。
推荐 3–5 个，每个给匹配理由、IF、分区、审稿周期、Aims&Scope 契合点、拒稿风险。

### S5 模板适配

```bash
python scripts/journals/fetch_template.py --journal "<name>" --out 05-template/template/
python scripts/render/render_latex.py --ir <rewritten.json> --template 05-template/template/ --out 05-template/build/
python scripts/render/render_docx.py  --ir <rewritten.json> --out 05-template/build/main.docx
```

模板获取失败时的三级降级策略见 `prompts/05-template-adaptation.md` 的「异常处理」节
（官方站点 → 出版商通用模板 → `assets/templates/` 内置骨架），降级必须在报告中显式声明。

### S6 多轮校验

最多 `max_rounds` 轮（默认 4），每轮跑全套检查器，把 `severity=error` 的项修掉后重跑，
直到 0 error 或达到轮次上限：

```bash
python scripts/validate/check_citations.py     --build 05-template/build/ --out 06-validate/cite.json
python scripts/validate/check_figures_tables.py --build 05-template/build/ --out 06-validate/figtab.json
python scripts/validate/check_equations.py      --build 05-template/build/ --out 06-validate/eq.json
python scripts/validate/latex_compile_check.py  --build 05-template/build/ --out 06-validate/compile.json
```

**Gate G6 是硬门控**：残留 error 时禁止标记为「可投稿」，必须在报告首页列出阻塞项。

### S7 结果汇报

```bash
python scripts/report/build_report.py --workdir runs/demo --out 07-report/conversion-report.md
```

报告必含：转换摘要、逐章修改记录、质量评分卡、期刊推荐表、校验结果、
`[[MISSING]]` 待补清单、投稿前 checklist（`assets/checklists/submission-checklist.md`）。

## 关键约束速查

- 图表：原文位图无法矢量化时，不要静默降级，写入 `gaps` 提示作者提供源文件
- 参考文献：`.bib` 的 key 统一 `firstauthorYEARfirstword` 格式，避免重复 key
- 单位与量纲：统一 SI，混用时以原文首次出现为准并记录进 `symbol_map`
- 中文残留：S6 会扫描 CJK 字符，成稿中出现即为 `error`
- 任何降级、跳过、自动修复都必须写入 `audit.jsonl`，报告中如实呈现

## 参考资料

需要时按需读取，不必一次全读：

- `references/sci-writing-conventions.md` — SCI 各章节写法与常见拒稿雷区
- `references/math-modeling-to-paper-mapping.md` — 建模报告 → 论文的章节/内容映射表
- `references/journal-database.md` — 期刊库字段说明与扩充方法
- `references/troubleshooting.md` — 常见故障与恢复手册
- `docs/architecture.md` — 数据流、状态机、质量门控完整说明


<!-- ====================================================================== -->
<!-- ADDITIVE SCI EXTENSION — appended 2026-08-19; legacy prefix is immutable -->
<!-- ====================================================================== -->

# Integrated SCI Writing Extension — 撰写 / 润色 / 投稿检索

> **兼容性声明**：从文件开头到本扩展标记之前的全部内容是原始 v1.0.0 Skill，
> 其 9,679-byte 前缀继续按字节保护。本扩展增加能力；后续为修复运行时/文档错误而修改的
> 原有代码文件必须进入 `config/preservation-manifest.json` 的显式 bug-fix allowlist，并由
> `python scripts/check_preservation.py` 对照 Git 基线检查。该机制是**兼容性回归保护**，
> 不是防篡改或安全认证。

新增模块先读取 `prompts/00-extension-router.md`，由它决定进入 W / P / J；它们是 Agent 模块，
**不是** `scripts/run_pipeline.py` 中额外的 Python stage。若任务未经过 S1 形成 IR，不得声称
G2/G6 或其他 IR 门控已经自动执行。

## 扩展后的适用范围

除原有“数学建模报告 → SCI 论文”七阶段流程外，本 Skill 现在还可独立处理：

- **SCI 论文撰写**：研究逻辑、章节结构、论证链、结果—讨论组织；
- **语言润色**：语法、句式、学术语体、topic–stress、科学语气强度；
- **投稿与期刊检索**：期刊匹配、实时规范核验、投稿材料、格式 preflight、审稿回复。

**范围优先级说明**：对于命中新模块的请求，本扩展仅覆盖上文
“纯文献综述/从零研究规划/非建模类润色不适用”的旧范围限制；
它**不覆盖**任何原有的反幻觉、引用验证、数学语义、质量门控或审计要求。

## 模块路由

| 用户任务 | 主模块 | 与原有流程关系 |
|---|---|---|
| 数学建模报告转 SCI | `prompts/00-orchestrator.md` → S1–S7 | **完全沿用原流程** |
| 从材料撰写 SCI 论文/章节 | `prompts/00-extension-router.md` → `prompts/08-sci-writing.md` | Agent 独立模块 |
| 英文润色/深度学术润色 | `prompts/00-extension-router.md` → `prompts/09-language-polish.md` | Agent 独立模块 |
| 找期刊/比期刊/投稿规范 | `prompts/00-extension-router.md` → `prompts/10-submission-journal-search.md` | Agent 独立模块 |
| 混合任务 | router → W → P → J（按需） | 不虚构未执行的 runtime gate |

所有新增模块首先读取：
`prompts/shared/05-integrity-preservation.md`。

## 新增不可协商约束：数学建模内容零损失

对数学建模文章，无论执行“撰写 / 润色 / 投稿检索”中的哪一个模块，都必须完整保留：

1. **所有图片**：图像对象、图号、图题、图注及其信息关系；
2. **所有表格**：结构、表号、表题、表注、数据、单位；
3. **所有公式**：公式内容、编号、符号、变量定义、约束与数学语义；
4. **所有核心结论**；
5. **所有关键论述与支撑链条**；
6. **所有关键数值、误差、不确定度、单位、范围与条件**。

不得以“更简洁”“更适合期刊”“减少篇幅”“提高可读性”为理由自行删改、精简或重写。
如果期刊规范与保护内容冲突，标记 `[[JOURNAL_CONFLICT]]` 并交由作者决定。

## 统一证据纪律

新增模块统一使用以下来源层级：

`SOURCE_CONFIRMED` → `USER_CONFIRMED` → `VERIFIED_EXTERNAL` →
`INFERRED` / `SUGGESTED` → `MISSING`

- 观测/数据事实与机制解释必须分开；
- 推断不得伪装为观测；
- 缺数据时保留 `[[MISSING]]`；
- 新增文献必须可验证；
- IF、分区、APC、收录、模板、投稿要求等时效信息必须在任务发生时重新检索并记录日期。

## Module W：SCI 撰写

读取 `prompts/08-sci-writing.md`。

核心流程：
1. 建立 source ledger 与保护清单；
2. 锁定 Research Question → Gap → Approach → Evidence → Contribution；
3. 按章节 rhetorical moves 写作；
4. Results 坚持 `Claim → Evidence → Quantification → Boundary`；
5. Discussion 坚持“观察 → 解释 → 机制（必要时避险）→ 对比 → 替代解释/局限 → 意义”；
6. 用 reviewer-perspective 五维自检，但不以总分掩盖缺失证据。

## Module P：语言润色

读取 `prompts/09-language-polish.md`。

核心流程：
1. 确定 proofread / academic polish / structural polish；
2. 冻结 LaTeX、公式、引用、数字、单位、图表引用和术语；
3. 先做科学语义冻结，再做语言优化；
4. 校准因果与 hedging；
5. 优化 topic–stress、旧→新信息、强动词与句式节奏；
6. 全文或 LaTeX 工程采用“保护 → 安全切分 → 润色 → 重组 → diff/一致性审计”。

## Module J：投稿与期刊检索

读取 `prompts/10-submission-journal-search.md`。

核心流程：
1. 建立 manuscript profile；
2. 候选发现 + scope/article-type 硬过滤；
3. 为每个候选建立实时证据卡；
4. 用 scope / method / evidence / audience / format / practical / indexing 多因子评分；
5. 推荐 3–5 个有梯度的真实候选，并写明风险；
6. 锁定期刊后生成 Guide for Authors compliance matrix；
7. 准备 Cover Letter、声明、Highlights/Graphical Abstract（仅在需要时）；
8. preflight 后再投稿；
9. 审稿阶段用 point-by-point、可定位的 response workflow。

## 开源调研与来源

完整候选仓库、star 快照、许可证判断、可复用能力和整合决策见：

`references/open-source-skill-survey.md`

整合遵循：
- MIT 来源：只做通用化重实现，并在调研文档归因；
- GPL / 未声明许可 / 许可不明确来源：**只借鉴工作流思想，不复制代码、模板或大段 prompt**；
- 本仓库仍按原 MIT License 发布。

## 完整性验证

更新后可执行：

```bash
python scripts/check_docs.py
python scripts/check_preservation.py
pytest -q
```

检查含义：
- 原始 `SKILL.md` 的 9,679-byte 前缀必须保持字节级一致；
- 有 Git 历史时，从 v1.0.0 基线枚举全部原有文件，禁止删除，任何修改必须进入显式 bug-fix allowlist；
- 无 Git 历史时只做前缀与关键路径的降级检查，并明确提示验证范围受限；
- `check_docs.py` 同时检查配置/文档声明的关键脚本、示例、workflow 与资源路径是否真实存在。

这套机制用于发现兼容性回归与文档漂移；它**不**构成密码学防篡改证明。真正的论文科学内容保护还要依赖 IR/source ledger、G2/G6 和 `shared/05-integrity-preservation.md`。