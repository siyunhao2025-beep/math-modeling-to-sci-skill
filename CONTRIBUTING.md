# 贡献指南

感谢你想让这个项目变得更好。下面是参与方式，以及一些能省下双方时间的约定。

## 最需要帮助的地方

按价值排序：

1. **扩充期刊库** — `config/journals.yaml` 目前只有种子数据，这是最容易上手、收益最高的贡献
2. **补充期刊模板骨架** — `assets/templates/`，尤其是应用数学、运筹、工业工程方向的常投期刊
3. **改进提示词** — `prompts/`，如果你发现某个阶段输出质量不稳定，带上失败案例来提 Issue 或 PR
4. **解析器鲁棒性** — `scripts/ingest/`，真实世界的 `.docx` 千奇百怪，欢迎带上（脱敏的）问题样本
5. **补充领域知识** — `references/`，各学科的 SCI 写作惯例差异很大

## 开发环境

```bash
git clone https://github.com/<your-fork>/math-modeling-to-sci-skill.git
cd math-modeling-to-sci-skill
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

提交前本地跑一遍：

```bash
ruff check .                       # lint
ruff format --check .              # 格式
pytest -q --cov=scripts            # 测试
python scripts/validate/validate_ir.py --ir examples/output/manuscript.ir.json
python scripts/run_pipeline.py --input examples/input/sample-model-report.tex \
    --workdir /tmp/ci-demo --mode dry-run     # 端到端冒烟
```

CI 会跑同样的检查（`.github/workflows/ci.yml`）。

## 分支与提交

**分支命名**

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/overleaf-export` |
| `fix/` | 修 bug | `fix/docx-nested-list-parse` |
| `prompt/` | 提示词调整 | `prompt/s3-scoring-calibration` |
| `journals/` | 期刊库/模板 | `journals/add-ieee-tits` |
| `docs/` | 文档 | `docs/clarify-ir-schema` |
| `refactor/`、`test/`、`chore/` | 其余 | |

**提交信息**用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <简短描述>

[可选正文：为什么这么改，而不是改了什么]

[可选 footer：Closes #123 / BREAKING CHANGE: ...]
```

`type`：`feat` `fix` `docs` `style` `refactor` `test` `chore` `prompt` `journals`
`scope`：`s1`…`s7` / `ingest` / `validate` / `journals` / `render` / `report` / `config` / `ci`

示例：

```
fix(ingest): 修复 docx 嵌套列表导致章节层级错乱

python-docx 对多级列表返回的 style.name 不含层级信息，改为读取
numPr/ilvl 判定缩进层级。

Closes #47
```

```
prompt(s3): 校准创新性评分的锚点描述

原描述在 6-8 分区间过于宽泛，同一篇稿子多次评估波动可达 2 分。
补充了三个分数锚点的具体判据与反例。
```

## Pull Request 流程

1. 从 `main` 切分支
2. 保持 PR 聚焦——一个 PR 解决一件事，混合改动会被要求拆分
3. 补上测试（改了 `scripts/` 就得有对应 `tests/`）
4. 更新受影响的文档（改了 IR 结构必须同步 schema + README + `docs/architecture.md`）
5. 在 `CHANGELOG.md` 的 `[Unreleased]` 下加一行
6. 填完 PR 模板，特别是「如何验证」一节
7. CI 全绿后等 review

**会被直接关掉的 PR**：无说明的大规模格式化、夹带无关改动、破坏 schema 兼容性且无迁移说明、
往仓库里塞出版商模板文件（版权问题，见 [LICENSE](LICENSE) 附注）。

## 扩充期刊库

在 `config/journals.yaml` 的 `journals` 下追加条目，字段说明见
[`references/journal-database.md`](references/journal-database.md)：

```yaml
  - id: apm-elsevier
    name: Applied Mathematical Modelling
    publisher: Elsevier
    issn: "0307-904X"
    scope_tags: [applied-mathematics, mathematical-modelling, simulation,
                 optimization, engineering-applications]
    method_tags: [ode-pde, numerical-simulation, optimization, statistical-modelling]
    impact_factor:
      value: 4.4
      year: 2024                      # 必填：数据年份
      source: "JCR 2024"              # 必填：来源
      retrieved: "2026-08-19"         # 必填：采集日期
    quartile: Q1
    jcr_category: "Mathematics, Applied"
    review_weeks: [10, 16]            # 区间，非单值
    open_access: hybrid
    template:
      latex: "https://www.elsevier.com/authors/policies-and-guidelines/latex-instructions"
      docx: null
      bundled_fallback: elsevier-generic
    submission_url: "https://www.editorialmanager.com/apm/"
    notes: "偏好有明确工程应用背景的建模工作；纯理论推导易被拒。"
```

硬性要求：

- `impact_factor` 三个元数据字段（`year` / `source` / `retrieved`）**不可省略**。
  没有可靠来源就填 `null`，不要写猜测值。
- `review_weeks` 用区间而非单值，没有公开数据就填 `null`。
- `notes` 里写**可操作的投稿经验**（偏好/雷区），不写主观评价。
- 加完跑 `pytest tests/test_match_journals.py` 确认没破坏匹配逻辑。

## 改进提示词

提示词是这个项目的核心资产，改动要求比代码更严：

- **必须附失败案例**：说明「什么输入 → 原提示词产生什么问题输出 → 新提示词产生什么」
- **保持结构**：每个阶段提示词必须包含角色设定 / 输入契约 / 执行步骤 / 输出契约 /
  质量约束 / 异常处理 六个部分，不要删节
- **不破坏 IO 契约**：改了输出字段就得同步 `config/schema/` 和下游提示词的输入契约
- **反幻觉条款不可弱化**：`[[MISSING]]` / `[[UNVERIFIED_REF]]` 机制、
  "不臆造数据" 约束属于底线，任何弱化它们的 PR 不会被合并

衔接逻辑见 [`prompts/README.md`](prompts/README.md)。

## Schema 变更

修改 `config/schema/*.json` 属于破坏性变更，需要：

1. 递增 `schema_version`（IR 内字段）
2. 在 `docs/architecture.md` 的「Schema 演进」节写迁移说明
3. `CHANGELOG.md` 标 `BREAKING CHANGE`
4. 更新 `examples/output/` 下所有示例产物
5. 检查所有读取该 schema 的脚本与提示词

## 版本管理

遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)：

- **MAJOR** — IR schema 不兼容变更、阶段划分调整、CLI 参数破坏性变更
- **MINOR** — 新增阶段能力、新增期刊/模板、新增校验器、提示词能力增强
- **PATCH** — bug 修复、文档、期刊数据刷新、提示词措辞优化

发版流程（维护者）：

1. `CHANGELOG.md` 把 `[Unreleased]` 归档为新版本号 + 日期
2. 同步更新 `VERSION` 与 `SKILL.md` frontmatter 的 `version`
3. `git tag -a v1.2.0 -m "..."` && `git push origin v1.2.0`
4. `release.yml` 自动建 GitHub Release 并打包 skill 归档

## 报 Bug

用 [Issue 模板](.github/ISSUE_TEMPLATE/)，尽量给到：

- 输入文件类型与特征（能脱敏提供样本最好）
- 完整命令与 `--mode`
- `audit.jsonl` 相关片段
- 期望行为 vs 实际行为
- 环境：OS、Python 版本、是否装了 TeX

## 行为准则

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 一条底线

这个项目的定位是**写作与格式化辅助**。任何试图把它变成「代写论文」「伪造数据」
「绕过期刊 AI 披露政策」的功能请求或 PR，都会被拒绝。学术诚信不是可配置项。
