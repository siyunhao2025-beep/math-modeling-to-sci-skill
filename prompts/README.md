# prompts/ — 提示词体系说明

本目录包含两类提示词：

1. **数学建模报告 → SCI 论文的 S1–S7 主流程提示词**；
2. **通用 SCI 撰写 / 润色 / 投稿检索扩展模块（W/P/J）**。

提示词是给 Agent 执行者看的指令。Python CLI 只负责确定性解析、匹配、渲染、校验、报告与质量门控；它不会暗中调用 LLM。

## 设计原则

1. **单一职责**：S1–S7 每阶段一个主提示词；W/P/J 各自独立。
2. **结构化衔接**：S1–S7 通过 IR / JSON 文件传递，不依赖对话记忆。
3. **反幻觉贯穿**：缺数据、缺证据、未验证引用不能被生成内容替代。
4. **门控即契约**：S1–S6 的质量门控定义在 `config/quality-gates.yaml`，由 `scripts/gates.py` 实际求值。
5. **科学内容保护**：W/P/J 必须加载 `shared/05-integrity-preservation.md`；有 IR 时还受 G2/G6 等运行时检查约束。
6. **不夸大运行能力**：08/09/10 是 Agent 模块，不是 `run_pipeline.py` 的额外 Python stage。

---

## 目录结构

```text
prompts/
├── README.md
├── 00-orchestrator.md             # 数学建模 S1–S7 编排器
├── 00-extension-router.md         # W/P/J 扩展模块路由
├── 01-ingest-parse.md             # S1 输入解析
├── 02-academic-rewrite.md         # S2 学术化改写
├── 03-quality-assessment.md       # S3 独立质量评估
├── 04-journal-matching.md         # S4 期刊匹配
├── 05-template-adaptation.md      # S5 模板适配
├── 06-multi-round-validation.md   # S6 多轮校验
├── 07-final-report.md             # S7 汇报
├── 08-sci-writing.md              # W：通用 SCI 撰写
├── 09-language-polish.md          # P：语言润色 / 去 AI 味 / 语义保护
├── 10-submission-journal-search.md# J：选刊 / 投稿 / 审稿回复
└── shared/
    ├── role-preamble.md
    ├── io-contract.md
    ├── error-handling.md
    ├── glossary.md
    └── 05-integrity-preservation.md
```

---

## 一、S1–S7 主流程加载规则

| 阶段 | 主提示词 | 必加载 shared | 附加加载 |
|---|---|---|---|
| S0 | `00-orchestrator.md` | role-preamble, io-contract | error-handling（按需） |
| S1 | `01-ingest-parse.md` | role-preamble, io-contract | glossary |
| S2 | `02-academic-rewrite.md` | role-preamble, io-contract | `references/sci-writing-conventions.md`, `references/math-modeling-to-paper-mapping.md`, `config/style-rules.yaml` |
| S3 | `03-quality-assessment.md` | role-preamble, io-contract | `config/quality-gates.yaml` |
| S4 | `04-journal-matching.md` | role-preamble, io-contract | `config/journals.yaml`, `references/journal-database.md` |
| S5 | `05-template-adaptation.md` | role-preamble, io-contract | `assets/templates/*` |
| S6 | `06-multi-round-validation.md` | role-preamble, io-contract | `config/style-rules.yaml`, `assets/checklists/format-checklist.md` |
| S7 | `07-final-report.md` | role-preamble, io-contract | `assets/checklists/submission-checklist.md` |

### S1–S7 数据流

```text
S1 manuscript.ir.json
 ↓ G1
S2 manuscript.rewritten.json + references.bib
 ↓ G2
S3 assessment.json
 ↓ G3
S4 journal-match.json
 ↓ G4
S5 build/ + MANIFEST.json
 ↓ G5
S6 validation-final.json
 ↓ G6
S7 conversion-report.md
```

实际门控结果额外写入：

```text
<workdir>/gate-results/G1.json ... G6.json
```

**重要**：`config/quality-gates.yaml` 不再只是给模型看的说明；Python 运行时通过 `scripts/gates.py` 对 S1–S6 的配置条件逐项求值。无法求值的 error 级条件不得静默当作 PASS；只有配置明确允许 skip/degrade 的条件可以降级。

---

## 二、W/P/J 扩展模块

扩展模块入口是 `00-extension-router.md`。

| 模块 | 文件 | 用途 | 是否属于 CLI S1–S7 |
|---|---|---|---|
| W | `08-sci-writing.md` | 研究逻辑、章节组织、Results/Discussion 写作 | 否 |
| P | `09-language-polish.md` | 语法、学术语体、hedging、去 AI 味、LaTeX 保护 | 否 |
| J | `10-submission-journal-search.md` | 期刊检索、投稿规范、Cover Letter、审稿回复 | 否 |

W/P/J 必须加载：

- `shared/role-preamble.md`
- `shared/05-integrity-preservation.md`

如果处理的不是 S1 解析产生的 IR，不得声称 G2/G6 已自动执行。此时应建立 source ledger / protected spans，显式保护公式、数字、单位、引用、图表引用与科学结论强度。

### 常见组合

```text
通用 SCI 草拟 + 润色：W → P
润色 + 选刊：P → J
通用完整投稿准备：W → P → J
数学建模报告转 SCI：S1–S7；若用户还需要额外精修/投稿材料，再接 P/J
```

---

## 三、占位符机制

| 占位符 | 含义 | 处理原则 |
|---|---|---|
| `[[MISSING]]` | 原文缺失、作者需补 | 不得用生成内容填空 |
| `[[UNVERIFIED_REF]]` | 引用尚未验证 | 不得写入最终可投稿参考文献 |
| `[[?]]` / `??` | 编号或引用未解析 | S6 前必须解决或明确阻塞 |

G6 对可投稿成稿中的这些占位符零容忍。

---

## 四、Python CLI 与 Agent 的边界

- S1、S4、S5、S6、S7 有确定性 Python 实现。
- S2、S3 是 Agent/LLM 推理任务。
- `--ai-stub` 只是 demo/test：S2 原样透传，S3 生成 schema-valid 占位评估；报告必须标记 `DEMO_ONLY_NOT_SUBMISSION_READY`。
- `--no-ai-stub` 的含义是：**读取已经由 Agent 生成的真实 S2/S3 文件**。它不是“打开真实 AI API”的开关。

详见 `docs/architecture.md` 与 `references/troubleshooting.md`。

---

## 五、如何扩展

### 新增 S1–S7 类 Python 阶段

必须同时更新：

1. `config/pipeline.yaml`
2. 对应 prompt
3. 输出 schema（如需要）
4. `config/quality-gates.yaml`
5. `scripts/gates.py` 对应 check 实现
6. tests
7. `scripts/check_docs.py` 能检查到的路径

### 新增 Agent 模块

1. 新建模块 prompt；
2. 在 `00-extension-router.md` 登记；
3. 在本 README 登记；
4. 明确是否有 IR / runtime gate 支撑，禁止把纯提示词约束描述成已执行的代码检查。

### 修改公共科研底线

优先修改 `shared/role-preamble.md` / `shared/05-integrity-preservation.md`，并增加对应测试或门控；不要只在 README 中增加宣传性声明。

---

## 六、静态一致性检查

提交前至少运行：

```bash
python scripts/check_docs.py
python scripts/check_preservation.py
pytest -q
```

其中 `check_docs.py` 用于阻止“文档写了一个路径，但仓库中根本不存在”的问题再次出现。
