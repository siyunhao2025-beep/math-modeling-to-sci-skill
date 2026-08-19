# prompts/ — 提示词体系说明

本目录包含将"数学建模结果文章"转换为"可发表 SCI 论文"所需的全部提示词。
这些提示词是**给 AI 执行者（Skill 调用模型）看的指令**，不是给用户读的文档。

## 设计原则

1. **单一职责**：每个阶段一个文件，互不耦合，可单独加载、单独迭代。
2. **强衔接**：阶段间通过磁盘上的结构化文件（IR / JSON）传递，而非上下文记忆，
   避免"传话游戏"式的信息衰减与幻觉。
3. **反幻觉贯穿**：`shared/role-preamble.md` 的五条底线在每一阶段被强制前置加载。
4. **门控即契约**：每个提示词的"门控"段落直接对应 `config/quality-gates.yaml` 的判定条件，
   提示词不重新定义标准，只解释如何满足。
5. **可中断可续跑**：每阶段输入/输出文件明确，编排器可用 `--stage` 从任意阶段重启。

---

## 目录结构

```
prompts/
├── README.md                      # 本文件
├── 00-orchestrator.md             # S0 编排器：状态机、门控决策、模式差异、重试策略
├── 01-ingest-parse.md             # S1 输入解析（Word/LaTeX → IR）
├── 02-academic-rewrite.md         # S2 学术化改写（体裁转换 + 文献/动机/创新点）
├── 03-quality-assessment.md       # S3 质量评估（六维评分卡）
├── 04-journal-matching.md         # S4 期刊匹配与推荐
├── 05-template-adaptation.md      # S5 模板适配与重组
├── 06-multi-round-validation.md   # S6 多轮校验（零错误硬门控）
├── 07-final-report.md             # S7 结果汇报
└── shared/                        # 公共片段，被各阶段前置加载
    ├── role-preamble.md           # 五条不可违反底线（反幻觉核心）
    ├── io-contract.md             # 通用 IO 规则、ID 命名、占位符规范、审计契约
    ├── error-handling.md          # 全流程异常矩阵（E1~E6 / EG）
    └── glossary.md                # 术语表（建模 vs 论文对照、出版/写作术语）
```

---

## 加载规则（谁加载什么）

编排器（`00-orchestrator.md` 的"阶段提示词加载表"）规定：

| 阶段 | 主提示词 | 必加载 shared | 附加加载 |
|------|----------|---------------|----------|
| S0 | `00-orchestrator.md` | role-preamble, io-contract | error-handling（按需） |
| S1 | `01-ingest-parse.md` | role-preamble, io-contract | glossary |
| S2 | `02-academic-rewrite.md` | role-preamble, io-contract | references/sci-writing-conventions.md, references/math-modeling-to-paper-mapping.md, config/style-rules.yaml |
| S3 | `03-quality-assessment.md` | role-preamble, io-contract | config/quality-gates.yaml |
| S4 | `04-journal-matching.md` | role-preamble, io-contract | config/journals.yaml, references/journal-database.md |
| S5 | `05-template-adaptation.md` | role-preamble, io-contract | assets/templates/* |
| S6 | `06-multi-round-validation.md` | role-preamble, io-contract | config/style-rules.yaml, assets/checklists/format-checklist.md |
| S7 | `07-final-report.md` | role-preamble, io-contract | assets/checklists/submission-checklist.md |

**原则**：`shared/` 片段每次都加载（保证底线一致）；`references/`、`config/`、`assets/` 仅在对应阶段加载，避免长文档占满上下文。

---

## 阶段间数据流（衔接逻辑）

```
S1 ── manuscript.ir.json ──────────────┐
       (gaps, symbol_map)              │
S2 ── manuscript.rewritten.json ───────┤  S3 只读 rewritten 内容（不看 rewrite_log）
       (rewrite_log, gaps)             │       ↓ assessment.json
S3 ── assessment.json ─────────────────┤
       (total_score, tier, tags)       │
S4 ── journal-match.json ──────────────┤  recommendations[0] 驱动 S5/S6
       (recommendations, IF, risks)    │
S5 ── build/main.* + references.bib ───┤  MANIFEST.json 记录映射
       + MANIFEST.json + unmapped.json │
S6 ── validation-final.json ───────────┤  error_count → 状态标签
       (summary, blockers)             │
S7 ── conversion-report.md ◀───────────┘  汇聚全部产物
```

**关键衔接约束**（详见 `shared/io-contract.md`）：
- 文件是唯一的真相来源；阶段不依赖"上一轮我跟你说过"。
- 每个输出文件原子写入（`.tmp` → `replace`），并立即做 schema 校验。
- 不合格不出阶段，不进入下一阶段。

---

## 占位符机制（反幻觉的统一语言）

所有"我不确定 / 原文缺失"的情况，统一用占位符，绝不编造：

| 占位符 | 含义 | 谁产生 | 谁清除 |
|--------|------|--------|--------|
| `[[MISSING]]` | 内容缺失（原文没有，改写需要） | S2 | S6（删断言并进 gaps） |
| `[[UNVERIFIED_REF]]` | 引用无法验证 | S2 | S6（删引用并进待补清单） |
| `[[?]]` / `??` | 编号/引用未解析 | S5/S6 | S6 |

S6 门控 G6-06 零容忍这些占位符出现在提交稿中。

---

## 如何扩展本提示词体系

- **新增阶段**：在 `00-orchestrator.md` 状态机与加载表登记，新增 `0n-*.md`，
  并在 `config/quality-gates.yaml` 加对应 G 门控、`config/schema/` 加输出 schema。
- **改进某阶段提示词**：直接编辑对应 `0n-*.md`，保持"角色/输入/步骤/输出/质量约束/异常/自检"七段结构。
- **调整公共底线**：只改 `shared/role-preamble.md`，所有阶段自动生效。
- **扩充期刊库**：改 `config/journals.yaml`（见 `CONTRIBUTING.md`），S4 自动受益。

详见仓库根 `CONTRIBUTING.md` 与 `README.md`。
