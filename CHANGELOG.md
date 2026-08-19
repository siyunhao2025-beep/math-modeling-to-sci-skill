# Changelog

本文件记录项目的显著变更。版本号遵循 Semantic Versioning；根目录 `VERSION` 表示项目发行版本，`SKILL.md` 头部的 legacy `version: 1.0.0` 因兼容性保护暂不改动。

## [Unreleased]

### Added
- 后续改动在此记录。

## [1.2.0] - 2026-08-19

本版本针对两轮严格代码/学术工程审查，把外部审查提出的 18 个风险从“人工提示词”进一步落成可回归验证的代码、文档与 CI 约束。

### Added

- `scripts/readiness/pipeline_bridge.py` — 自动从已有 S1–S7 workdir 解析 IR、BibTeX、S4 期刊/ISSN、build 路径并运行可确定执行的 S8 检查；缺少当前官方期刊证据时显式阻塞，不猜测。
- `scripts/audit_repo.py` — 18 项仓库风险回归审计：S8 孤儿、文档路径、门控、兼容 CLI 命名空间、prompt 漏登记、preservation 治理、CI 等。
- `prompts/shared/06-user-guidance-playbook.md` — 新手从上传 Word/LaTeX 开始的逐步中文提示词；支持“继续/下一步/按完整流程执行”。
- S8 Publication Readiness Suite：真实引用、citation support、deep journal fit、Claim–Evidence、图表、方法/统计/伦理、Reviewer Simulator、Submission Preflight。

### Changed

- `scripts/run_pipeline.py` — 在真实 Agent S2/S3 模式下，进入 S7 前通过 S8 bridge 自动尝试投稿就绪检查；新增 `--readiness auto|required|off` 与可选 similarity precheck。`--ai-stub` 仍只用于 demo，并不会被当作真实稿件送去 S8。
- `scripts/readiness/run_readiness.py` — 从“手工填写 --ir/--bib/--issn/--aims-scope-file ...”改为只要求 `--workdir`；其余均为高级 override。
- `README.md` / `prompts/README.md` — 同步 S1–S8、W/P/J、用户引导、CLI/Agent 边界、当前期刊证据要求和兼容命名约定。
- `scripts/check_docs.py` — 从单个坏路径黑名单升级为全 Markdown `scripts/*.py` 路径核验、完整 prompt inventory 核验，以及 compatibility shim package-shadow 检查。
- `scripts/check_preservation.py` / `config/preservation-manifest.json` — 在原 v1.0.0 baseline 外增加 extension baseline 治理；继续明确这只是兼容性回归守卫，不是密码学防篡改证明。
- `examples/input/sample-model-report.tex` — 明确标为 legacy compatibility alias；新文档统一使用 `sample-modeling-report.tex`。

### Fixed

- 防止 S8 功能存在但主流程完全无法到达。
- 防止 `scripts/ingest.py` 与 `scripts/ingest/` 等兼容路径被误改成同名 import package。
- 修复 prompt README 未登记 `06-user-guidance-playbook.md` 的漂移。
- 修复旧 Changelog 将实际 `scripts/audit.py` 错写成 `scripts/audit/logger.py` 的问题。
- 移除旧 Changelog 中对未存在 `release.yml` / Dependabot 配置的过度声明；当前 CI 以 `.github/workflows/ci.yml` 和 `.github/workflows/validate-skill.yml` 为准。

## [1.1.0] - 2026-08-19

### Added

- W/P/J：SCI Writing、Language Polish、Journal & Submission 扩展。
- Scientific Content Preservation Contract 与兼容性回归检查。
- 可执行 G1–G6 `GateEvaluator`。
- S8 Publication Readiness 的首版 prompt/工具层。

### Fixed

- 修正原始文档中的阶段脚本路径/示例路径兼容问题。
- 补齐 `docs/architecture.md` 与 `references/troubleshooting.md`。
- `--no-ai-stub` 明确为“读取真实 Agent 产物”，不再暗示 CLI 内置 LLM 调用。

## [1.0.0] - 2026-08-19

首个完整版本：七阶段 S1–S7、提示词体系、结构化 IR、质量评分、期刊种子匹配、模板适配、多轮校验和审计日志骨架。

主要入口：

- `SKILL.md`
- `prompts/00-orchestrator.md`
- `config/pipeline.yaml`
- `config/quality-gates.yaml`
- `scripts/run_pipeline.py`
- `scripts/ingest.py`
- `scripts/journals.py`
- `scripts/render.py`
- `scripts/validate.py`
- `scripts/report.py`
- `scripts/audit.py`

兼容命令位于 package-less 子目录，例如 `scripts/ingest/parse_latex.py`、`scripts/journals/match_journals.py`、`scripts/validate/check_citations.py`；这些是 thin CLI shims，不是第二套独立 Python package 实现。

当前自动化工作流：

- `.github/workflows/ci.yml`
- `.github/workflows/validate-skill.yml`

[Unreleased]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/compare/master...HEAD
[1.2.0]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/releases
[1.1.0]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/releases
[1.0.0]: https://github.com/siyunhao2025-beep/math-modeling-to-sci-skill/releases
