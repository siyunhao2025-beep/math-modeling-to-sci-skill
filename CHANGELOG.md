# Changelog

本文件记录项目的所有显著变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- （在此追加你的变更）

## [1.0.0] - 2026-08-19

首个完整版本。七阶段流水线、提示词体系、质量门控与审计机制全部就位。

### Added

**Skill 与文档**
- `SKILL.md` — Skill 入口，含触发条件、五条核心设计原则、分阶段执行指引
- `README.md` — 完整用途/用法/输入输出规范说明，含 Mermaid 流程图
- `docs/architecture.md` — 数据流、状态机、质量门控、Schema 演进策略
- `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `LICENSE`（含期刊模板版权附注）

**七阶段提示词体系**
- `prompts/00-orchestrator.md` — 总控编排器，含状态机与门控决策逻辑
- `prompts/01-ingest-parse.md` — 输入解析（Word/LaTeX → IR），语义角色标注
- `prompts/02-academic-rewrite.md` — 学术化改写，体裁转换 + 文献综述 + 创新点声明
- `prompts/03-quality-assessment.md` — 六维评分卡与改进项生成
- `prompts/04-journal-matching.md` — 期刊匹配，带证据与拒稿风险评估
- `prompts/05-template-adaptation.md` — 模板适配与三级降级策略
- `prompts/06-multi-round-validation.md` — 多轮校验，迭代至零 error
- `prompts/07-final-report.md` — 成稿与转换报告生成
- `prompts/shared/` — 角色前言、IO 契约、异常处理、术语表四个公共片段
- `prompts/README.md` — 提示词衔接逻辑与数据流转说明

**数据契约**
- `config/schema/manuscript.schema.json` — IR schema（v1.0）
- `config/schema/assessment.schema.json` — 质量评估 schema
- `config/schema/journal-match.schema.json` — 期刊推荐 schema
- `config/schema/audit-log.schema.json` — 审计事件 schema

**配置**
- `config/pipeline.yaml` — 阶段编排、依赖、超时、重试策略
- `config/quality-gates.yaml` — G1–G6 六个门控的阈值与失败动作
- `config/journals.yaml` — 期刊种子库（含 IF 年份/来源/采集日期元数据）
- `config/style-rules.yaml` — 学术语言规则（时态、语态、禁用词、模糊限定词）

**脚本层**
- `scripts/run_pipeline.py` — CLI 编排入口，支持 `auto`/`interactive`/`dry-run` 三模式、
  按阶段续跑、快照回退、审计查看
- `scripts/ingest/` — `detect_format.py`、`parse_docx.py`、`parse_latex.py`
- `scripts/validate/` — `validate_ir.py`、`check_citations.py`、
  `check_figures_tables.py`、`check_equations.py`、`latex_compile_check.py`
- `scripts/journals/` — `match_journals.py`（多因子加权匹配）、`fetch_template.py`（三级降级）
- `scripts/render/` — `render_latex.py`、`render_docx.py`
- `scripts/report/build_report.py` — 八段式转换报告生成
- `scripts/audit/logger.py` — append-only JSONL 审计日志

**资产与示例**
- `assets/templates/` — IEEE / Elsevier / Springer 三套内置骨架（降级兜底，非出版商原件）
- `assets/checklists/` — 格式、引用、投稿前三份清单
- `references/` — SCI 写作惯例、建模报告→论文映射表、期刊库说明、故障手册
- `examples/` — 示例输入与全套输出产物
- `tests/` — 覆盖格式检测、LaTeX 解析、IR 校验、期刊匹配、引用检查

**CI/CD**
- `.github/workflows/ci.yml` — ruff lint + 多版本 pytest + 端到端冒烟
- `.github/workflows/validate-skill.yml` — SKILL.md frontmatter 与 schema 一致性校验
- `.github/workflows/release.yml` — tag 触发打包与 Release
- Issue / PR 模板，含期刊模板申请专用模板
- `dependabot.yml`

### Security
- `.gitignore` 默认排除 `*.docx` / `*.pdf` / `.env`，防止误提交他人稿件与凭据
- 所有外部检索结果落盘存证于 `04-journals/journal-evidence/`，可复核

[Unreleased]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/releases/tag/v1.0.0
