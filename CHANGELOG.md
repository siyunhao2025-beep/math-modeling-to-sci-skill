# Changelog

本文件记录项目的显著变更。版本号遵循 Semantic Versioning；根目录 `VERSION` 表示项目发行版本。

## [Unreleased]

### Added
- 后续改动在此记录。

## [2.0.0] - 2026-09-22

本版本将原有“七阶段转换 + 后置扩展”重构为统一的 **FORGE × TRACE** 体系，并融合 Ku-academic 与 Huaweibei-cool 中经过筛选的证据工程、变更传播和模型验证能力。

### Added

- FORGE 五阶段：Fidelity、Opportunity、Revalidation、Grounding、Editorial。
- TRACE 五条横向质量轨：可追溯、严谨、论证、合规、证据。
- `scripts/forge.py`：非破坏性的工作区初始化、阶段门、状态汇总与变更影响传播。
- 八类模型原型验证矩阵、图表契约、引用身份/支持双检与访问深度规则。
- `config/forge-trace.yaml`、FORGE 项目 schema、独立回归测试与 UI 元数据。
- 全新品牌定位、广告语与主视觉。

### Changed

- 将“数学内容零损失”改为“零静默损失”：原始资产全部可追溯，但无关内容可经记录和作者确认后移出正文。
- 图表数量由 claim coverage 决定，不采用固定图数或强制技术路线图。
- `SKILL.md` 改为当前规范允许的两字段 frontmatter，并把详细规则按需拆入 references。
- S1–S8 降为兼容运行时，由 FORGE 统一研究逻辑与阶段门语义。

### Fixed

- Windows 控制台 Unicode 退出信息导致的运行时崩溃。
- Windows 路径分隔符导致的 readiness bridge 测试失败。
- 旧版 skill 前缀保护阻止架构升级的问题。

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
- 修复旧 Changelog 曾把实际 `scripts/audit.py` 误写成一个并不存在的 `audit/logger.py` 子路径的问题。
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
