<div align="center">

# math-modeling-to-sci-skill

**把数学建模报告系统转换为 SCI 稿件，并在投稿前做证据、期刊 fit 与审稿人视角审查**

支持 Word / LaTeX / LaTeX 工程；保留原始 S1–S7 转换流水线，并增加 W/P/J 学术写作模块与 S8 Publication Readiness Suite。

[![CI](https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/actions/workflows/ci.yml)
[![Validate Skill](https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/actions/workflows/validate-skill.yml/badge.svg)](https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/actions/workflows/validate-skill.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

</div>

---

## 不知道怎么提问？

直接上传你的 `.docx` / `.tex` / LaTeX `.zip`，然后发一句：

> **开始第一步**

Skill 会先做**只读体检**，不急着改正文：确认文章类型、结构、图表、公式、引用、核心结论与主要风险，再告诉你下一步。如果希望一路执行到投稿前审查，可以发：

> **按完整流程执行**

每一步结束后，Skill 会只给你一个最推荐的下一步和一段可直接复制的中文提示词。完整新手引导维护在 [`prompts/shared/06-user-guidance-playbook.md`](prompts/shared/06-user-guidance-playbook.md)。

---

## 这个项目解决什么问题

数学建模报告和 SCI 论文不是同一种体裁。前者围绕“解题过程”，后者需要明确的研究问题、研究缺口、方法证据链、结果边界、文献定位和投稿规范。本项目把转换与投稿前检查拆成可追踪的阶段，并坚持三条底线：

- **不补造研究事实**：原文缺失内容用 `[[MISSING]]` / `[[AUTHOR_CHECK]]` 暴露；
- **不把未验证引用写成真引用**：S8 可用 Crossref 为主、Semantic Scholar / PubMed 辅助核验 DOI/元数据；
- **不为了“写得更像 SCI”破坏科学内容**：公式、变量、关键数值、图表、核心结论和论证强度受保护。

它不替作者做未完成的实验，不伪造伦理批号/数据链接，也不预测或保证录用。

---

## 当前能力

### S1–S7：数学建模报告 → SCI 论文

```text
S1 解析 → G1 → S2 学术化改写 → G2 → S3 质量评估 → G3
  → S4 期刊候选 → G4 → S5 模板适配 → G5 → S6 多轮校验 → G6
                                                            ↓
                                               S8 投稿就绪审查（推荐）
                                                            ↓
                                                    S7 最终报告/投稿包
```

- S1：解析 Word/LaTeX/ZIP，建立 IR 与图表/公式/引用清单；
- S2：Agent 将报告体转换为 SCI 论证结构；
- S3：六维质量评估；
- S4：本地 seed 只负责候选初筛，时效性期刊信息必须再核验；
- S5：模板适配；
- S6：引用/图表/公式/编译/CJK/格式等硬检查；
- G1–G6：由 [`scripts/gates.py`](scripts/gates.py) 真正求值，失败会按配置重试、降级或阻断；
- S7：根据真实 artifacts 生成保守的最终状态报告。

### W / P / J：通用 SCI 扩展

- **W — SCI Writing**：Research Question → Gap → Approach → Evidence → Contribution；
- **P — Language Polish**：学术英文、去 AI 套话、hedging、时态/句式，同时冻结公式/数字/引用；
- **J — Journal & Submission**：期刊检索、Guide for Authors、Cover Letter、投稿材料、审稿回复。

路由见 [`prompts/00-extension-router.md`](prompts/00-extension-router.md)。

### S8：Publication Readiness Suite

S8 重点检查“能不能经得住编辑和审稿人追问”，而不只是语言是否漂亮：

1. **Reference Reality Layer**：DOI/元数据真实性、严格 clean BibTeX；
2. **Citation Depth Audit**：文献是否真的支持正文对应 claim；
3. **Deep Journal Fit**：当前官方 Aims & Scope、Article Type、近 12 个月公开期刊记录、desk-reject 风险；
4. **Claim–Evidence Audit**：关键定量/比较/因果/机制结论映射到图表、公式、数据、统计或验证文献；
5. **Figure/Table Audit**：正文引用、caption、轴/单位/误差棒/尺度/数值一致性与视觉风险；
6. **Methods/Statistics/Reporting/Ethics**：方法、统计、报告规范、伦理与数据/代码可用性；
7. **Reviewer Simulator + Rebuttal Loop**：模拟编辑、领域、方法统计和挑剔审稿人，生成实质性质疑与修订回路；
8. **Submission Preflight**：汇总全部证据，只输出 `BLOCKED` / `AUTHOR_ACTION_REQUIRED` / `READY_FOR_HUMAN_SUBMISSION_CHECK`。

`READY_FOR_HUMAN_SUBMISSION_CHECK` 只表示自动/Agent 预检未发现既定阻塞项，**不是录用保证**。

---

## 快速开始

### 安装

```bash
git clone https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill.git
cd math-modeling-to-sci-skill
pip install -r requirements.txt
```

LaTeX 投稿建议额外安装 TeX Live / MiKTeX，使真实编译检查可用。

### 作为 Agent Skill 使用

把仓库放进你的 Agent Skill 目录后，直接上传稿件并说：

> 请先不要改正文，完整读取我上传的 Word/LaTeX，做一次投稿前体检，然后按 Skill 的流程告诉我下一步。

或者：

> 按完整流程执行：从解析、SCI 化改写、质量评估、期刊筛选、模板适配、技术校验，到 S8 引用/证据/期刊 fit/模拟审稿和最终 preflight。

### 作为命令行工具使用

CLI **不会自己调用 LLM**。S2/S3 的真实产物需要 Agent 先写入 workdir；默认 `--ai-stub` 只用于 demo/test。

```bash
# Demo：只验证 deterministic 流程，不代表真实 SCI 评估
python scripts/run_pipeline.py \
  --input examples/input/sample-modeling-report.tex \
  --workdir runs/demo \
  --mode dry-run

# 真实 Agent 已生成 S2/S3 后，从已有阶段继续；S8 在进入 S7 前自动尝试
python scripts/run_pipeline.py \
  --workdir runs/my-paper \
  --stage S4 \
  --no-ai-stub \
  --readiness auto

# 严格模式：只要 S8 未达到 READY_FOR_HUMAN_SUBMISSION_CHECK 就返回非零
python scripts/run_pipeline.py \
  --workdir runs/my-paper \
  --stage S4 \
  --no-ai-stub \
  --readiness required

# 只运行 S8；只需 workdir，其余信息会优先从已有 artifacts 自动解析
python scripts/readiness/run_readiness.py --workdir runs/my-paper

# 显式关闭 S8（例如只做 legacy 转换）
python scripts/run_pipeline.py --workdir runs/my-paper --stage S4 --no-ai-stub --readiness off

# 查看全链路审计
python scripts/run_pipeline.py --workdir runs/my-paper --show-audit
```

S8 的期刊官方证据不会被猜测。推荐约定放到：

```text
runs/my-paper/04-journals/journal-evidence/
├── aims-scope.txt
├── article-types.txt
└── target-journal.json
```

`target-journal.json` 可记录 `journal_name`、`issn`、`scope_source_url`、`article_type`、`article_type_source_url`。缺失当前官方证据时，S8 会明确阻塞而不是伪造 PASS。

---

## 输入输出

### 支持输入

| 格式 | 支持 | 说明 |
|---|---|---|
| Word `.docx` | ✅ | 标准 OOXML |
| LaTeX `.tex` | ✅ | 单文件 |
| LaTeX `.zip` | ✅ | 多文件工程，自动定位主文件 |
| Markdown `.md` | 实验性 | 可转 IR |
| PDF | 不作为主输入 | 为避免公式/图表/引用结构丢失，优先提供源文件 |

### 典型 workdir

```text
runs/my-paper/
├── 00-input/
├── 01-parse/manuscript.ir.json
├── 02-rewrite/manuscript.rewritten.json
├── 03-assess/assessment.json
├── 04-journals/
│   ├── journal-match.json
│   └── journal-evidence/
├── 05-template/
│   ├── MANIFEST.json
│   └── build/main.tex
├── 06-validate/validation-final.json
├── 08-readiness/
│   ├── resolved-inputs.json
│   ├── readiness-run.json
│   ├── reference-verification.json
│   ├── references.clean.bib
│   ├── citation-support-audit.json
│   ├── journal-fit.json
│   ├── claim-evidence-audit.json
│   ├── figure-table-audit.json
│   ├── compliance-audit.json
│   ├── reviewer-simulation.json
│   └── submission-preflight.json
├── conversion-report.md
└── audit.jsonl
```

Agent-only artifacts（如 citation-support、Reviewer Simulator、视觉科学判断）不会由 Python 用空壳文件冒充完成；缺失时 preflight 会保持阻塞或要求作者处理。

---

## 期刊匹配：不要误读本地 seed

[`config/journals.yaml`](config/journals.yaml) 是**候选种子库**，不是实时 JCR 数据库。CLI 的 S4 可以离线初筛，但 IF、分区、APC、Article Type、Aims & Scope、模板和收录状态都可能变化。面向实际投稿的判断必须由 J/S8 在任务发生时重新核验当前权威来源，并记录检索日期。

因此：

- 本地 S4 `match_score` ≠ 接收概率；
- seed IF/分区 ≠ 当前已核验指标；
- 期刊投稿 URL ≠ Aims & Scope 证据；
- Crossref 的近期记录是 published/online records，不等同于 accepted manuscripts。

---

## 科学内容与反幻觉保护

扩展模块统一读取 [`prompts/shared/05-integrity-preservation.md`](prompts/shared/05-integrity-preservation.md)。核心保护对象包括：

- 所有图片/表格及编号、caption、单位；
- 所有公式、变量、定义、约束；
- 所有关键数值、误差、不确定度、范围和符号；
- 核心结论与关键论证链；
- 引用 key、DOI/URL、交叉引用；
- 直接观测与机制推断的语气强度。

期刊规范与受保护科学内容冲突时使用 `[[JOURNAL_CONFLICT]]`，交给作者决定。

---

## 质量门控与真实性边界

- G1–G6：[`config/quality-gates.yaml`](config/quality-gates.yaml) + [`scripts/gates.py`](scripts/gates.py)；
- S8 最终门：[`scripts/readiness/submission_preflight.py`](scripts/readiness/submission_preflight.py)；
- 兼容性回归：[`scripts/check_preservation.py`](scripts/check_preservation.py)，明确**不是**密码学防篡改机制；
- 两轮外部审查的 18 项风险回归：[`scripts/audit_repo.py`](scripts/audit_repo.py)。

---

## 开发者回归检查

提交 PR 前运行：

```bash
python -m compileall -q scripts tests
python scripts/check_docs.py
python scripts/audit_repo.py
python scripts/check_preservation.py
pytest -q
```

CI 会重复这些检查，避免“文档写了但代码不存在”“新增 prompt 没登记”“S8 又变成孤儿”“兼容 CLI 变成同名 Python package”等问题回归。

---

## 名称与版本

- **仓库/发行名**：`math-modeling-to-sci-skill`
- **Skill 标识**：`math-modeling-to-sci`
- 项目发行版本以根目录 [`VERSION`](VERSION) 为准。

Skill 标识与仓库名的差异是为了保持原始 v1.0.0 `SKILL.md` 前缀兼容性，不是两个不同项目。不要为了统一名字而破坏旧 Skill 调用入口。

---

## 许可证与贡献

MIT License。开放 Issue / PR。开源能力调研与许可证处理说明见 [`references/open-source-skill-survey.md`](references/open-source-skill-survey.md)。

如果这个 Skill 对你的论文转换、投稿前检查或审稿回复有帮助，欢迎点一个 **Star ⭐** 支持项目继续迭代。
