# prompts/ — 提示词体系说明

本目录包含四类提示词：

1. **数学建模报告 → SCI 论文的 S1–S7 主流程提示词**；
2. **通用 SCI 撰写 / 润色 / 投稿检索扩展模块（W/P/J）**；
3. **S8 Publication Readiness Suite**：真实引用、深度期刊 fit、Claim–Evidence Audit、图表审查、Reviewer Simulator、方法/伦理合规与一键投稿前总审查；
4. **shared 共享策略/用户引导**：科学内容保护、I/O 契约、错误处理、术语表和新手逐步提示词。

提示词是给 Agent 执行者看的指令。Python CLI 负责确定性解析、匹配、渲染、校验、API 元数据核验、结构化审查与总审查聚合；它不会暗中调用 LLM。

## 设计原则

1. **单一职责**：S1–S7 每阶段一个主提示词；W/P/J 与 S8 子模块各自独立。
2. **结构化衔接**：主流程与 readiness artifacts 通过 IR / JSON 文件传递。
3. **反幻觉贯穿**：缺数据、缺证据、未验证引用不能被生成内容替代。
4. **门控即契约**：S1–S6 的质量门控由 `scripts/gates.py` 实际求值；S8 的投稿就绪阻塞条件由 `scripts/readiness/submission_preflight.py` 聚合执行。
5. **科学内容保护**：所有扩展模块必须加载 `shared/05-integrity-preservation.md`。
6. **代码/Agent 边界清楚**：引用元数据、词法 fit、结构审查、preflight 可由 Python 确定性执行；语义引用支持、Claim–Evidence 真正含义、图表科学性与 Reviewer Simulator 属于 Agent 任务。
7. **不夸大能力**：最强自动状态是 `READY_FOR_HUMAN_SUBMISSION_CHECK`，不输出“保证录用”或虚假接收概率。
8. **新手可直接使用**：用户不知道怎么提问时，加载 `shared/06-user-guidance-playbook.md`，默认先只读体检，再给一个可复制的下一步提示词。

---

## 目录结构

```text
prompts/
├── README.md
├── 00-orchestrator.md                  # 数学建模 S1–S7 编排器
├── 00-extension-router.md              # W/P/J/S8 扩展路由
├── 01-ingest-parse.md                  # S1
├── 02-academic-rewrite.md              # S2
├── 03-quality-assessment.md            # S3
├── 04-journal-matching.md              # S4
├── 05-template-adaptation.md           # S5
├── 06-multi-round-validation.md        # S6
├── 07-final-report.md                  # S7
├── 08-sci-writing.md                   # W
├── 09-language-polish.md               # P
├── 10-submission-journal-search.md     # J
├── 11-publication-readiness-orchestrator.md # S8 总编排
├── 12-reference-depth-audit.md         # 引用真实性 + 上下文支持
├── 13-journal-fit-deep.md              # 深度期刊 fit / desk-reject 风险
├── 14-claim-evidence-audit.md          # Claim–Evidence Audit
├── 15-figure-table-audit.md            # 图表科学审查
├── 16-reviewer-simulator.md            # Reviewer Simulator + rebuttal loop
├── 17-submission-preflight.md          # 一键投稿前总审查
├── 18-methods-reporting-ethics.md      # 规范/统计/伦理/可复现性
└── shared/
    ├── role-preamble.md
    ├── io-contract.md
    ├── error-handling.md
    ├── glossary.md
    ├── 05-integrity-preservation.md
    └── 06-user-guidance-playbook.md
```

### shared 命名约定

为保持 v1.0.0 兼容性，四个最早的 shared 文件继续使用无编号名称；从扩展策略开始使用 `05-`、`06-` 递增编号。**这不是两套独立实现**，也不要为了“看起来整齐”重命名旧文件，因为已有 prompt 会引用它们。后续新增跨模块强制策略/工作手册继续采用编号前缀。

---

## 一、S1–S7 主流程

| 阶段 | 主提示词 | 主要输出 |
|---|---|---|
| S1 | `01-ingest-parse.md` | `manuscript.ir.json` |
| S2 | `02-academic-rewrite.md` | `manuscript.rewritten.json` + `.bib` |
| S3 | `03-quality-assessment.md` | `assessment.json` |
| S4 | `04-journal-matching.md` | `journal-match.json` |
| S5 | `05-template-adaptation.md` | `build/` + `MANIFEST.json` |
| S6 | `06-multi-round-validation.md` | `validation-final.json` |
| S7 | `07-final-report.md` | `conversion-report.md` |

数据流：

```text
S1 → G1 → S2 → G2 → S3 → G3 → S4 → G4 → S5 → G5 → S6 → G6
                                                               ↓
                                                      S8 readiness（可选/推荐）
                                                               ↓
                                                        S7 final report
```

G1–G6 实际结果写入 `<workdir>/gate-results/G1.json ... G6.json`。

---

## 二、W/P/J 扩展模块

| 模块 | 文件 | 用途 |
|---|---|---|
| W | `08-sci-writing.md` | 研究逻辑、章节组织、Results/Discussion 写作 |
| P | `09-language-polish.md` | 学术英语、hedging、去 AI 味、LaTeX/数字保护 |
| J | `10-submission-journal-search.md` | 期刊检索、投稿规范、Cover Letter、审稿回复 |

常见组合：W → P；P → J；W → P → J。未经过 S1 的普通稿件只能使用 protected-span/source-ledger 保护，不能声称 IR 门控已经运行。

---

## 三、S8 Publication Readiness Suite

S8 是**逻辑上的 post-S6 readiness 层**，不改写 legacy `config/pipeline.yaml` 的 S1–S7 编号。入口：`11-publication-readiness-orchestrator.md`。

### S8 与主 CLI 的真实关系

`scripts/run_pipeline.py` 现在在真实 S2/S3 模式、进入 S7 前调用 `scripts/readiness/pipeline_bridge.py`。桥接器会自动从 workdir 解析 IR、BibTeX、S4 选刊、ISSN 和 build 路径，然后执行能够确定性完成的 S8 检查。`scripts/readiness/run_readiness.py` 也只要求 `--workdir`，其余参数均为高级覆盖项。

```bash
# 已有完整 workdir：自动解析并运行确定性 S8
python scripts/readiness/run_readiness.py --workdir runs/my-paper

# 主流程：真实 Agent S2/S3 + S8 自动预检
python scripts/run_pipeline.py --workdir runs/my-paper --stage S4 --no-ai-stub --readiness auto

# 把 S8 未完成/未通过视为命令失败
python scripts/run_pipeline.py --workdir runs/my-paper --stage S4 --no-ai-stub --readiness required
```

**重要**：官方 Aims & Scope、Article Type 等当前期刊证据不会从本地 seed 或投稿 URL 猜测。缺失时 bridge 会产生明确 blocker，等待 Agent/作者提供当前官方证据，而不是把步骤标成 PASS。Crossref/Semantic Scholar/PubMed 网络不可用、限流或无结果时也必须降级为“无法验证”，不能静默通过。

### S8 模块与确定性工具

| 功能 | Agent prompt | Python 工具 |
|---|---|---|
| 真实引用层 | `12-reference-depth-audit.md` | `scripts/readiness/reference_verifier.py` |
| 引用深度/上下文支持 | `12-reference-depth-audit.md` | Agent semantic audit + `citation-support-audit.json` |
| 深度期刊 fit | `13-journal-fit-deep.md` | `scripts/readiness/journal_fit.py` |
| Claim–Evidence Audit | `14-claim-evidence-audit.md` | `scripts/readiness/claim_evidence.py` |
| 图表审查 | `15-figure-table-audit.md` | `scripts/readiness/figure_table_audit.py` |
| Reporting/Methods/Ethics | `18-methods-reporting-ethics.md` | `scripts/readiness/compliance_audit.py` |
| Reviewer Simulator + rebuttal | `16-reviewer-simulator.md` | Agent structured artifact |
| 出版级语言检查 | `09-language-polish.md` | `scripts/readiness/language_check.py`（LanguageTool server 可选） |
| 相似度预检 | S8 orchestrator | `scripts/readiness/similarity_precheck.py`（advisory only） |
| 官方模板 provenance | S8 orchestrator | `scripts/readiness/template_fetch.py` |
| 一键投稿前总审查 | `17-submission-preflight.md` | `scripts/readiness/submission_preflight.py` |

### S8 产物

统一写入 `<workdir>/08-readiness/`：

```text
resolved-inputs.json
readiness-run.json
reference-verification.json
references.clean.bib
citation-support-audit.json
journal-fit.json
claim-evidence-audit.json
figure-table-audit.json
compliance-audit.json
reviewer-simulation.json
language-audit.json              # optional
similarity-precheck.json         # optional
template-provenance.json         # LaTeX final check
submission-preflight.json
submission-preflight.md
```

### S8 真值边界

- API 元数据确认“这篇文献是谁/是什么”，不能自动证明“它支持这句话”；后者必须做上下文引用核验。
- Crossref 的近期条目默认称“recent published/online records”，不能无依据写成 accepted articles。
- `journal_fit.py` 给的是可复现词法 baseline，不能替代 Agent 的语义 scope 判断。
- Reviewer Simulator 是模拟，不是真实同行评议。
- Semantic Scholar similarity precheck 不是 iThenticate / Turnitin / 查重百分比。
- `submission_preflight.py` 只允许三种状态：`BLOCKED` / `AUTHOR_ACTION_REQUIRED` / `READY_FOR_HUMAN_SUBMISSION_CHECK`。

---

## 四、用户引导

当用户只上传 Word/LaTeX、说“帮我看看”“下一步”“我不知道怎么问”时，读取 `shared/06-user-guidance-playbook.md`。默认先做只读体检，不直接改科学内容；每阶段完成后只给一个最推荐的下一步和一段可复制中文提示词。用户只回复“继续”时，从已有 artifacts 推断下一合法阶段。

---

## 五、占位符机制

| 占位符 | 含义 | 处理原则 |
|---|---|---|
| `[[MISSING]]` | 原文缺失、作者需补 | 不得用生成内容填空 |
| `[[UNVERIFIED_REF]]` | 引用尚未验证 | 不得进入最终可投稿参考文献 |
| `[[JOURNAL_CONFLICT]]` | 期刊要求与受保护内容冲突 | 作者决策 |
| `[[AUTHOR_CHECK: ...]]` | 证据/伦理/科学内容冲突需作者判断 | 不自动改科学事实 |

---

## 六、Python CLI 与 Agent 边界

- S1、S4、S5、S6、S7 有确定性 Python 实现。
- S2、S3 是 Agent/LLM 推理任务；`--no-ai-stub` 是“读取真实 Agent 产物”，不是“启动某个 LLM API”。
- S8 中引用 API、词法 fit、结构审查、合规预筛、preflight 是确定性工具；语义 citation support、Claim–Evidence 最终判断、视觉科学审查、Reviewer Simulator 需要 Agent。
- `--ai-stub` 只用于 demo/test，且不会自动把 demo 输出送去 S8 冒充真实稿件。

---

## 七、扩展与静态一致性

新增能力至少同步：prompt/router、配置/阻塞策略、Python 工具或 Agent-only 边界、tests、`scripts/check_docs.py`、`config/preservation-manifest.json`。

提交前运行：

```bash
python scripts/check_docs.py
python scripts/audit_repo.py
python scripts/check_preservation.py
python -m compileall -q scripts tests
pytest -q
```

其中 `check_docs.py` 阻止断链/漏登记；`audit_repo.py` 把两轮外部审查的 18 个风险变成回归检查；`check_preservation.py` 是兼容性回归守卫，不是密码学防篡改证明。
