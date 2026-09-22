---
name: math-modeling-to-sci
description: 将已有数学建模报告、竞赛论文、技术建模文档或可复现实验工程转化为证据可追溯、方法经复核、面向真实期刊的 SCI 稿件。用于 Word/LaTeX/Markdown/项目文件的只读体检、体裁重构、研究问题与贡献重定位、模型再验证、引用双重核验、图表与论证链设计、期刊匹配、模板适配、模拟审稿、返修和投稿前检查。尤其适用于 MCM/ICM、国赛、华为杯等建模成果转论文；不用于凭空补实验、伪造引用、保证录用或把普通英文润色冒充研究升级。
---

# Math Modeling to SCI · M²SCI Forge

> 不把建模报告翻译成英文；把模型证据锻造成经得起审稿的 SCI 论文。

## 先做判断，再做转换

先读取用户已有文件和工作区，不重复询问已知信息。默认从只读诊断开始；只有用户明确要求改稿时才修改正文。

先判断以下前提是否成立：

1. 已有材料包含真实模型、数据、结果或可复现代码，而不只是方案设想。
2. 结果具有超出竞赛题解的研究问题、方法价值或可迁移发现。
3. 关键结论能回链到数据、代码运行、图表、公式或已核验文献。
4. 缺口可通过补分析、补验证或收窄主张解决，而非依赖虚构内容。

若以上条件明显不成立，直接给出 `NOT_READY_FOR_CONVERSION`，列出最小补强清单。不要把语言润色包装成 SCI 升级。

## 使用 FORGE × TRACE 框架

先读 `references/forge-trace-framework.md`。按五个阶段推进：

| 阶段 | 目标 | 关键产物 |
|---|---|---|
| **F · Fidelity** | 冻结原始事实，建立可追溯底座 | source manifest、资产清单、处置账本、符号表 |
| **O · Opportunity** | 把“解题任务”重构为可研究问题 | research positioning、贡献上限、模型画像 |
| **R · Revalidation** | 按模型原型补齐期刊级证据 | validation plan、运行记录、稳健性与边界 |
| **G · Grounding** | 把证据组织成论文论证链 | claim map、稿件、图表契约、引用双检 |
| **E · Editorial** | 匹配真实期刊并通过投稿前审查 | journal evidence、评审面板、preflight |

同时用 TRACE 五条横向质量轨检查每个阶段：

- **T · Traceability**：主张、数字、公式、图表与来源可定位。
- **R · Rigor**：设计、基线、公平比较、不确定性与稳健性充分。
- **A · Argument**：问题—缺口—方法—证据—贡献链成立。
- **C · Compliance**：期刊、伦理、披露、格式与材料要求有当前证据。
- **E · Evidence**：证据强度不低于句子强度，缺失显式暴露。

分数只能辅助排序，不能覆盖硬阻塞项。任一关键主张无证据、引用矛盾、结果不可复现或期刊规范未核实时，不得输出“可投稿”。

## 选择最短有效路线

| 用户意图 | 路线 | 读取 |
|---|---|---|
| 不知道能否转 SCI / 先评估 | F → O | `references/conversion-playbook.md` |
| 完整数模报告转 SCI | F → O → R → G → E | 本文件全部路由 |
| 已有稿件，补严谨性与证据 | 从最早失效阶段回退 | `references/change-control.md` |
| 只做模型验证与实验补强 | O → R | `references/model-validation-matrix.md` |
| 只做引用、论证或图表审计 | G | `references/evidence-and-citation.md`、`references/figure-contract.md` |
| 只找期刊或做投稿前检查 | E | `references/editorial-fit-and-preflight.md` |
| 收到审稿意见 | 先做变更分级，再回退到 O/R/G/E | `references/change-control.md` |

如果用户只说“继续”，从现有工件推断下一合法阶段。只在真正需要作者裁决、缺关键证据或将发生不可逆外部动作时暂停。

## F · Fidelity：先冻结，再改写

1. 对输入做只读快照并记录 SHA-256、文件类型、时间和来源。
2. 机械提取章节、公式、符号、图、表、引用、关键数字、结论与附件。
3. 建立资产处置账本。对每项标记 `retain`、`adapt`、`supplement`、`drop` 或 `pending`。
4. 将“零损失”解释为**零静默损失**：原始信息必须可追溯，但无关竞赛内容不必强塞进期刊正文；删除或移入补充材料必须写明理由，实质性删除需作者确认。
5. 冻结数学语义、数值、单位、边界条件和证据强度。变量改名必须进入 `symbol_map` 并全文同步。

优先复用现有 S1 解析器与 IR。若输入无法解析，先报告能力边界，不要凭肉眼读到的局部内容声称完整解析。

## O · Opportunity：先证明值得写，再写

1. 把竞赛任务改写为一个主研究问题和最多三个子问题。
2. 明确 `Problem → Gap → Approach → Evidence → Contribution → Boundary`。
3. 把创新分成问题、方法、证据、应用四类；“使用了某算法”本身不算创新。
4. 识别主模型原型与辅原型：optimization、evaluation、prediction、classification-cv、mechanism、signal、spatial-graph、simulation。
5. 将原型匹配视为候选假设，不把关键词命中当作模型定论。
6. 给出贡献上限：`demonstrated`、`supported`、`suggested` 或 `not_supported`。不得用更强措辞越过证据。

若研究缺口只靠“尚未见报道”且没有系统检索证据，标为 `UNVERIFIED_GAP`；若问题只能复述题目答案，要求补外部有效性、一般化条件或方法比较。

## R · Revalidation：按原型补证据

读取 `references/model-validation-matrix.md`，先建立最简可信基线，再决定是否保留复杂模型。

执行以下共通检查：

1. 使用同一数据、预处理、划分、指标、随机种子/重复次数和计算预算做公平比较。
2. 区分训练、验证与最终测试；按时间、空间、主体或分组结构防止泄漏。
3. 分开处理观测、参数与情景不确定性。
4. 将每个高风险主张链接到至少一项适配验证；核心创新或高风险因果/机制主张优先使用两类独立证据。
5. 只有声称模块贡献时才做消融；不存在合理基线时改用理论界、精确解、小规模穷举、外部数据或独立实现互验。
6. 保留失败运行、负结果和方案取舍。没有真实运行文件时只能写“计划验证”，不得写成结果。

用户请求“优化模型”时，先比较收益、稳定性、复杂度和解释成本。差异未超过不确定性或收益不足以覆盖成本时，推荐保留更简单的基线。

## G · Grounding：以主张为单位造论文

1. 先建 claim map，再写正文。每个核心主张记录位置、证据、条件、风险与状态。
2. 按 `Claim → Evidence → Quantification → Boundary` 写 Results。
3. 按“观察 → 解释 → 对比 → 替代解释/局限 → 意义”写 Discussion；机制证据不足时主动降级因果措辞。
4. 将 Methods 与代码位置、配置、数据版本和运行记录对应。
5. 对引用做两道独立检查：
   - 身份核验：文献是否真实、元数据是否准确、版本是否规范；
   - 支持核验：文献是否在相同对象、范围、条件和证据层级下支持当前句子。
6. 按句子强度确定最低访问深度。定量与因果句必须读到全文并给页/图/表定位；只有摘要时收窄句子或标 `CANNOT_VERIFY`。
7. 按 claim coverage 规划图表。每张图回答一个科学问题，并具有 source data → script → output → caption → claim 的链路。不要按历史均值或用户期待硬凑数量。
8. 润色时冻结 LaTeX、公式、数字、单位、引用键、图表引用和术语。去 AI 味不得改变证据强度。

## E · Editorial：用当前证据做期刊决策

1. 先做 manuscript profile，再发现候选期刊。
2. 使用官方 Aims & Scope、article type、Guide for Authors 与近期论文做硬过滤和语义判断。
3. 对 IF、分区、APC、收录、模板、字数、数据/代码政策等时效信息实时核验，记录 URL 与检索日期。
4. 提供有梯度的 3–5 个候选，并分别写契合点、desk-reject 风险、证据缺口和作者成本；不要给录用概率。
5. 让 3–5 个不同角色独立评审，不把分数平均成一个漂亮总分。分歧本身进入作者决策。
6. 汇总确定性检查与语义检查。最强正面状态只能是 `READY_FOR_HUMAN_SUBMISSION_CHECK`。

投稿、付费、上传、发送邮件或对外共享文件需要用户明确授权。

## 不可协商的证据纪律

- 不编造数据、样本量、运行、显著性、伦理编号、引用、期刊指标或审稿结果。
- 不把 DOI 可解析等同于“该文支持这句话”。
- 不把相关写成因果，不把模拟写成观测，不把计划写成已完成。
- 不把脚本 schema PASS 写成科学有效性 PASS。
- 不静默删除原文资产，不静默降低门槛，不静默改变结果。
- 不承诺录用，不预测录用概率，不声称规避 AI 检测。
- 将无法验证的内容标为 `待确认`，同时写清已查内容、阻塞原因和下一步。

## 状态与交付

只使用以下顶层状态：

- `NOT_READY_FOR_CONVERSION`：研究基础不足，需先补模型/数据/验证。
- `BLOCKED`：存在不可绕过的证据、复现、引用或合规阻塞。
- `AUTHOR_ACTION_REQUIRED`：自动与代理工作已完成到作者决策点。
- `READY_FOR_HUMAN_SUBMISSION_CHECK`：可进入作者/导师的最终投稿复核，不代表录用。

每轮结束报告：已实现、已测试、语义人工复核待办、外部实时核验待办、阻塞项和唯一推荐下一步。不要把“文件已生成”“已解析”或“单元测试通过”说成研究结论已验证。

## 工具与兼容层

- 用 `python scripts/forge.py init|status|gate|impact` 管理 FORGE 工件与变更传播。
- 用 `python scripts/run_pipeline.py` 运行原有 S1–S7 兼容流水线。
- 用 `python scripts/readiness/run_readiness.py` 运行投稿就绪兼容检查。
- 需要旧阶段细节时读取 `prompts/00-orchestrator.md` 与 `references/legacy-stage-map.md`，不要同时加载全部旧提示词。

## 按需读取

- 框架、阶段门与目录：`references/forge-trace-framework.md`
- 体裁转换与研究重定位：`references/conversion-playbook.md`
- 八类模型再验证：`references/model-validation-matrix.md`
- 引用双检与证据等级：`references/evidence-and-citation.md`
- 图表契约：`references/figure-contract.md`
- 变更传播与回退：`references/change-control.md`
- 期刊匹配与投稿前检查：`references/editorial-fit-and-preflight.md`
- 旧 S1–S8 映射：`references/legacy-stage-map.md`
- 来源、许可与融合边界：`references/provenance.md`
