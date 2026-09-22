# FORGE × TRACE 框架

## 目录

1. [框架目的](#1-框架目的)
2. [五阶段与阶段门](#2-五阶段与阶段门)
3. [TRACE 横向质量轨](#3-trace-横向质量轨)
4. [工作目录与工件](#4-工作目录与工件)
5. [状态机](#5-状态机)
6. [人机分工](#6-人机分工)
7. [最小运行方式](#7-最小运行方式)
8. [完成定义](#8-完成定义)

## 1. 框架目的

FORGE 不是把现有报告按章节翻译成英文，而是连续回答五个问题：

1. **Fidelity**：原材料里究竟有什么，哪些内容不可静默改变？
2. **Opportunity**：现有题解能否形成具有外部意义的研究问题？
3. **Revalidation**：现有结果能否承受期刊审稿所需的对比、稳健性和不确定性检查？
4. **Grounding**：每个句子、图表和贡献能否回链到真实证据？
5. **Editorial**：该稿件是否符合某个真实期刊的范围、体裁和当前投稿要求？

FORGE 是阶段轴，TRACE 是质量轴。阶段向前推进，质量轨贯穿始终。

## 2. 五阶段与阶段门

### F · Fidelity / 事实保真

**输入**：`.docx`、`.tex`、LaTeX 工程、Markdown、数据、代码、图表或现有稿件。

**动作**：

- 建立输入快照、哈希和来源记录；
- 盘点章节、公式、符号、图、表、引用、数字、结论和附件；
- 建立 `disposition-ledger.json`，记录每项内容的去向；
- 标记缺失数据、不可解析对象和冲突；
- 建立符号、单位与关键事实锁。

**门 F**：

- 原始输入可定位且未被覆盖；
- 关键资产均有唯一 ID；
- 没有未解释的静默丢失；
- 公式、数字、单位、结论和图表具备来源位置；
- 解析范围与未解析范围均被披露。

**失败处置**：停留在 F。请求缺失文件、修复解析或让作者裁决冲突，不得直接改稿。

### O · Opportunity / 研究机会重构

**输入**：F 阶段资产、题目背景、已有研究目标和作者希望。

**动作**：

- 区分竞赛任务、研究问题和工程应用问题；
- 建立 Problem–Gap–Approach–Evidence–Contribution–Boundary 链；
- 识别主/辅模型原型；
- 建立贡献候选和证据上限；
- 进行转化可行性裁决。

**门 O**：

- 一个主问题可由现有或可补充的数据回答；
- 缺口不是未经检索的“没人做过”；
- 每项贡献对应可观察差异或可验证收益；
- 研究价值不只依赖竞赛排名、题目要求或复杂算法名称；
- 已区分 demonstrated、supported、suggested、not_supported。

**失败处置**：输出 `NOT_READY_FOR_CONVERSION`。给出最小补强路线，不继续生成完整论文。

### R · Revalidation / 再验证

**输入**：研究定位、模型画像、数据/代码和原始结果。

**动作**：

- 建立基线、主模型与必要改进链；
- 按数据结构做无泄漏划分；
- 设计公平比较、误差、不确定性、敏感性和稳健性分析；
- 按主张决定是否需要消融、外部验证、理论界或精确解；
- 保存运行配置、版本、随机种子、失败运行和结果文件。

**门 R**：

- 关键结论至少有一项适配验证；
- 核心创新或高风险结论具有第二条独立证据，或明确说明证据上限；
- 所有比较使用同口径数据、预算和指标；
- 结果可回链到运行记录，计划分析未冒充已完成；
- 负结果和不稳定性未被隐藏。

**失败处置**：停留在 R，或将主张降级后重新过 O 门。

### G · Grounding / 论证落地

**输入**：通过 R 的结果、文献证据和目标体裁。

**动作**：

- 建立 claim map、Methods map 和图表契约；
- 完成引言、方法、结果、讨论、结论与摘要；
- 对新增和原有引用执行身份与支持双检；
- 对数字、单位、公式、图表引用和主张强度做一致性审计；
- 完成语言与结构润色，同时冻结事实。

**门 G**：

- 所有核心主张可定位到项目结果或已核验证据；
- 定量/因果引用具备全文定位；
- 图表均有来源链、正文回链和科学问题；
- 摘要、正文、图表和结论中的数字一致；
- 没有把相关写成因果、把模拟写成观测、把推断写成事实。

**失败处置**：按缺陷来源回退到 O、R 或 G，不用语言包装掩盖证据缺口。

### E · Editorial / 编辑与投稿适配

**输入**：通过 G 的稿件、候选期刊与官方材料。

**动作**：

- 建立候选期刊实时证据卡；
- 进行范围、体裁、读者、方法、证据和合规匹配；
- 获取并验证官方模板与作者指南；
- 执行多角色模拟审稿和逐条修订；
- 生成投稿材料与 preflight。

**门 E**：

- 目标期刊的范围、体裁、模板和关键要求来自当前官方来源；
- 所有 blocker 已关闭或由作者明确接受并在投稿前人工处理；
- 3–5 个评审角色完成独立审查，科学覆盖充分；
- 投稿包内文件、匿名、声明、数据/代码、伦理和引用要求一致；
- 顶层状态最多为 `READY_FOR_HUMAN_SUBMISSION_CHECK`。

## 3. TRACE 横向质量轨

每个阶段都生成 TRACE 判定，不把五项简单求平均。

| 轨道 | 核心问题 | 典型阻塞 |
|---|---|---|
| Traceability | 能否定位来源、运行和版本？ | 无源数字、未记录改动、图表无数据链 |
| Rigor | 比较和验证是否公平、适配？ | 数据泄漏、无基线、错误统计单位 |
| Argument | 论证是否形成因果或逻辑闭环？ | 贡献与证据脱节、结果不能回答问题 |
| Compliance | 当前规范是否已核实？ | 过期模板、未核伦理/披露/匿名要求 |
| Evidence | 证据强度是否覆盖句子强度？ | 摘要支撑定量句、引用矛盾、机制过度声称 |

允许使用三态：`PASS`、`AUTHOR_ACTION_REQUIRED`、`BLOCKED`。只要存在关键阻塞，阶段总判定就是 `BLOCKED`；不要用高总分抵消。

## 4. 工作目录与工件

```text
workspace/
├─ forge-project.json
├─ 00-source/
│  ├─ source-manifest.json
│  └─ snapshot/
├─ 01-forensics/
│  ├─ asset-inventory.json
│  ├─ disposition-ledger.json
│  ├─ symbol-map.json
│  └─ gaps.json
├─ 02-opportunity/
│  ├─ research-positioning.json
│  └─ model-profile.json
├─ 03-revalidation/
│  ├─ validation-plan.json
│  ├─ run-log.json
│  └─ validation-results.json
├─ 04-manuscript/
│  ├─ claim-map.json
│  ├─ figure-manifest.json
│  ├─ citation-audit.json
│  └─ manuscript.*
├─ 05-editorial/
│  ├─ journal-evidence.json
│  ├─ reviewer-panel.json
│  └─ submission-preflight.json
└─ audit/
   ├─ events.jsonl
   └─ impact-report.json
```

旧 S1–S8 目录可继续存在。使用 `references/legacy-stage-map.md` 做兼容映射，不复制同一科学事实到两个互不一致的账本。

## 5. 状态机

```text
F → O → R → G → E
    ↑   ↑   ↑   ↑
    └── change impact / reviewer request / author decision ──┘
```

允许从现有材料对应阶段进入，但必须证明上游工件已具备同等信息。不能因为已有英文稿就跳过事实保真和证据审计。

发生变更时：

- 语言或排版改动留在 G/E；
- 主张强度变化回到 O/G；
- 数字、图表或分析变化回到 R；
- 数据、模型、参数或研究问题变化回到 F/O/R；
- 期刊要求变化留在 E，但可能触发 G 的篇幅与图表重排。

详细规则见 `references/change-control.md`。

## 6. 人机分工

**脚本可负责**：文件清单、哈希、schema、必填字段、引用格式、对象计数、依赖传播、编译、可重复的数值检查。

**代理需负责**：研究问题判断、主张语义、文献是否支持句子、模型假设是否成立、讨论是否过度、期刊语义契合。

**作者必须负责**：原始事实确认、实质删除、未公开数据授权、研究伦理、署名、目标期刊选择、投稿与对外发送。

任何一层不得冒充另一层已完成。

## 7. 最小运行方式

```bash
python scripts/forge.py init runs/paper --input report.docx --route full
python scripts/forge.py status runs/paper
python scripts/forge.py gate runs/paper F
python scripts/forge.py impact runs/paper --changed 03-revalidation/validation-results.json
```

`init` 只初始化可追溯工作区，不生成论文。`status` 只检查工件与确定性契约，不代表科学正确。`impact` 只计算登记的阶段依赖，语义影响仍需人工复核。

## 8. 完成定义

同时满足以下条件才可结束完整流程：

- F–E 工件齐全且对应门无 blocker；
- 关键主张、数字、图表、公式、引用与运行记录可追溯；
- 未验证内容已移出论证链或显式交给作者；
- 当前期刊要求已记录来源和日期；
- 模拟评审的重大问题已关闭；
- 最终状态为 `READY_FOR_HUMAN_SUBMISSION_CHECK`，并明确这不是录用保证。
