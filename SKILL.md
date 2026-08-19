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
