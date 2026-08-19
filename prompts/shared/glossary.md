# 术语表

> 统一本项目内部与学术写作场景的术语，避免各阶段理解偏差。

## 项目内部术语

| 术语 | 含义 |
|------|------|
| **IR**（Intermediate Representation） | 中间表示。`manuscript.ir.json`，全流程共享的结构化稿件表示 |
| **semantic_role** | 语义角色。章节在论文逻辑中的功能定位（如 `methodology`），不等于章节标题 |
| **Gate / 门控** | 阶段间的质量检查点。G1–G6，不通过则重试/回退/降级/阻塞 |
| **硬门控** | 不可跳过、不可降级的门控。本项目仅 G6 是硬门控 |
| **gap** | 内容缺口。原文缺失、需作者补充的内容，登记在 IR 的 `gaps` |
| **degrade / 降级** | 首选方案不可用时启用备选方案。必须记录并在报告披露 |
| **占位符** | `[[MISSING]]` / `[[UNVERIFIED_REF]]`，标记缺失而非填充内容 |
| **震荡**（oscillation） | S6 中同一问题反复出现修不掉的状态，触发转人工 |
| **workdir** | 一次运行的工作目录，含全部中间产物与审计日志 |
| **run_id** | 单次运行的唯一标识，用于审计日志关联 |
| **交叉验证** | 横向一致性检查（引用双向、数值、图表编号、符号定义） |

## 建模报告 vs SCI 论文的结构术语对照

| 建模报告常见叫法 | SCI 论文对应部分 | semantic_role |
|-----------------|-----------------|---------------|
| 摘要 | Abstract | `abstract` |
| 问题背景 / 问题重述 | Introduction（部分）+ Problem Statement | `introduction` / `problem_statement` |
| 问题分析 | Introduction 的研究缺口段 | `introduction` |
| 模型假设 | Assumptions（常并入 Methodology） | `assumptions` |
| 符号说明 | Nomenclature / Notation | `notation` |
| 模型建立 | Model Formulation / Methodology | `model_formulation` |
| 模型求解 | Solution Approach / Algorithm | `algorithm` |
| 结果分析 | Results | `results` |
| 模型检验 | Validation（并入 Experiments/Results） | `experiments` |
| 灵敏度分析 | Sensitivity Analysis | `sensitivity_analysis` |
| 模型评价 / 优缺点 | Discussion + Limitations | `discussion` / `limitations` |
| 模型推广 | Future Work | `future_work` |
| 参考文献 | References | `references` |
| 附录（代码、数据表） | Appendix / Supplementary Material | `appendix` |

**建模报告通常缺失、必须新增的部分**：
- Related Work（文献综述）— `related_work`
- Contributions（显式创新点声明）— 通常置于 `introduction` 末尾
- Data Availability / Conflict of Interest / AI Disclosure 等声明性章节

## 学术出版术语

| 术语 | 含义 | 备注 |
|------|------|------|
| **Aims & Scope** | 期刊征稿范围声明 | S4 匹配的首要依据 |
| **Guide for Authors** | 作者指南，含格式与投稿要求 | 优先级高于本项目的默认规则 |
| **Desk Reject** | 编辑初审直接拒稿，不送外审 | 常因 scope 不符或格式严重不规范 |
| **Major / Minor Revision** | 大修 / 小修 | |
| **IF**（Impact Factor） | 影响因子，JCR 发布，每年 6 月更新 | 本项目要求必带年份与来源 |
| **Quartile** | JCR 分区 Q1–Q4，按学科类别内排名百分位 | 同一刊在不同类别可有不同分区 |
| **中科院分区** | 中国科学院文献情报中心的分区，与 JCR 不同 | 国内考核常用，字段 `cas_division` |
| **APC**（Article Processing Charge） | 论文处理费，OA 期刊收取 | |
| **Gold OA** | 完全开放获取，作者付费 | |
| **Hybrid** | 混合模式，可选 OA（付费）或订阅（免费） | |
| **Green OA** | 允许作者自存档预印本 | |
| **Predatory Journal** | 掠夺性期刊，收费但无实质同行评审 | S4 必须排查 |
| **CRediT** | 贡献者角色分类标准，用于 Author Contributions | |
| **Cover Letter** | 投稿信 | 本项目 v1.0 暂不生成 |
| **Highlights** | 亮点，Elsevier 部分刊要求的 3–5 条要点 | |
| **Graphical Abstract** | 图形摘要 | |
| **ORCID** | 研究者唯一标识符 | |
| **DOI** | 数字对象唯一标识符 | 引用验证的首选依据 |
| **preprint** | 预印本（arXiv、SSRN 等） | 引用时须标注 |

## 学术写作术语

| 术语 | 含义 |
|------|------|
| **Research Gap** | 研究缺口。已有工作未解决/未覆盖的问题，是论文合法性的来源 |
| **Contribution** | 贡献。本文相对已有工作新增的东西，须可对比、可核验 |
| **Novelty** | 新颖性。与创新性近义，SCI 的核心门槛 |
| **Hedging** | 模糊限定。用 may/suggest/indicate 等表达不确定性，是学术诚信要求 |
| **Topic Sentence** | 主题句。段落首句概括本段论点 |
| **Signposting** | 路标语。引导读者理解结构（"Section 3 presents..."） |
| **Baseline** | 基线方法。对比实验的参照对象 |
| **Ablation Study** | 消融实验。逐个移除组件以验证各部分贡献 |
| **Reproducibility** | 可复现性。他人能否依据论文重现结果 |
| **booktabs** | LaTeX 三线表宏包，学术表格标准做法（无竖线） |

## 缩写速查

| 缩写 | 全称 |
|------|------|
| IR | Intermediate Representation |
| IF | Impact Factor |
| JCR | Journal Citation Reports |
| SCIE | Science Citation Index Expanded |
| OA | Open Access |
| APC | Article Processing Charge |
| DOI | Digital Object Identifier |
| MSC | Mathematics Subject Classification |
| OOXML | Office Open XML（.docx 的底层格式） |
| OMML | Office Math Markup Language（Word 公式格式） |
| CJK | Chinese-Japanese-Korean（中日韩字符） |
| MCM/ICM | Mathematical/Interdisciplinary Contest in Modeling |
| CUMCM | 全国大学生数学建模竞赛 |
