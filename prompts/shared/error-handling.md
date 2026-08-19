# 公共异常处理策略

> 覆盖全流程可能遇到的异常。每条给出：识别信号 → 处理动作 → 是否需披露。
> 未列出的异常按 `role-preamble.md` 的三级优先级原则处理。

## 决策总则

```
异常发生
   ↓
影响学术诚信？（数据真实性 / 引用真实性 / 数值准确性）
   ↓ 是                              ↓ 否
STOP + 报告 + 等人工              能降级继续？
（绝不猜测蒙混）                    ↓ 是        ↓ 否
                              降级 + 记录 + 披露   跳过 + 标记不可信 + 披露
```

**核心判据**：这个处理会不会让作者对稿件产生错误认知？会 → 必须披露。

---

## S1 输入解析阶段

### E1-01 文件格式无法识别
**信号**：`detect_format.py` 返回 `unknown`
**处理**：
1. 按扩展名猜测并尝试对应解析器
2. 全部失败 → 尝试当纯文本读取，走 markdown 路径
3. 仍失败 → **STOP**，报告"无法解析输入文件"，列出已尝试的方式与建议
   （如"检测到 .doc 旧格式，请另存为 .docx"）
**披露**：是

### E1-02 Word 公式是图片
**信号**：docx 中 `inline_shape` 位于公式典型位置，无对应 OMML
**处理**：
- 记录图片位置，在 IR 对应位置放 `{"type":"equation","latex":null,"flags":["MISSING"]}`
- `gaps` 登记 `category: unparseable_content`，`severity: high`
- `how_to_fix`: "请提供该公式的 LaTeX 源码或用 Word 公式编辑器重新录入"
- **不要**尝试 OCR 识别公式（错误率高且不可验证）
**披露**：是，且在报告中逐个列出位置

### E1-03 章节层级无法识别
**信号**：G1-02 触发（章节 < 3）
**处理**：按 `quality-gates.yaml#G1.on_fail.strategies_order` 依次尝试：
1. `heading_by_style` — 按 Word 样式名（Heading 1/2/3、标题 1/2/3）
2. `heading_by_format` — 按字号 + 加粗 + 独占段落 + 短文本的组合特征
3. `flat_fallback` — 全部段落归入单个 `sec-1`，`semantic_role: unclassified`，
   由提示词纯语义判定切分
**披露**：降级到 `flat_fallback` 时必须披露

### E1-04 LaTeX 主文件定位失败
**信号**：zip 中多个 `.tex` 含 `\documentclass`，或无任何 `\documentclass`
**处理**：
- 多个 → 选文件名匹配 `main|paper|manuscript|ms|article` 的；仍多个 → 选最大的，
  在 `parse-warnings.json` 记录选择理由与其他候选
- 无 → 选包含 `\begin{document}` 的；仍无 → 当作片段解析，不做完整文档假设
**披露**：是

### E1-05 自定义宏无法展开
**信号**：`\newcommand` 定义的宏在正文大量使用
**处理**：
- 收集所有 `\newcommand` / `\def` / `\DeclareMathOperator` 定义，存入 IR 的
  `provenance` 备注，并在 S5 生成成稿时一并携带到导言区
- 不尝试手工展开（易出错），保持原样
**披露**：仅在宏定义与目标模板冲突时披露

### E1-06 参考文献是手写而非 .bib
**信号**：`thebibliography` 环境，或 Word 中的纯文本文献列表
**处理**：逐条解析为结构化 `reference`，`origin: from_source`，
解析不出的字段填 `null`，`raw` 保留原始字符串
**披露**：解析失败条数 > 20% 时披露

---

## S2 学术化改写阶段

### E2-01 网络不可用，无法检索文献
**信号**：`WebSearch` / `WebFetch` 连续失败
**处理**：
- **不新增任何参考文献**
- 需要引用的位置一律标 `[[UNVERIFIED_REF: 描述所需文献]]`
- `gaps` 批量登记 `category: missing_reference`
- 报告中列出所有待补引用位置及推荐检索关键词
**披露**：必须，且报告首页显著标注"文献综述未完成，需联网补充"

### E2-02 原文缺少实验/验证内容
**信号**：无 `experiments` / `results` 语义角色的章节，或有但无数据
**处理**：
- **绝不编造实验**
- `gaps` 登记 `category: missing_experiment`、`severity: blocker`
- `how_to_fix` 写明期刊通常要求什么（如"至少与 2 个基线方法在公开数据集上对比，
  报告均值±标准差与显著性检验"）
- 继续改写其余部分，但 S3 的 `experimental_completeness` 会给低分，
  可能触发 G3 → 这是正确的行为
**披露**：必须，报告首页列为 blocker

### E2-03 原文创新点不明确
**信号**：通读全文找不到"本文与已有工作的区别"
**处理**：
- 不替作者宣称创新点
- 从原文中**提取**可能的创新候选（新的约束条件、新的场景组合、新的求解策略），
  以问句形式列在报告中请作者确认："以下哪些是您认为的核心创新？"
- 正文的 contributions 部分写入基于原文确有内容的表述，
  不确定的标 `flags: [NEEDS_AUTHOR_REVIEW]`
**披露**：是

### E2-04 中英混排、术语不统一
**信号**：`meta.language == "mixed"`，或同一概念出现多种译法
**处理**：
- 建立术语对照表，选定唯一译法（优先该领域权威文献的用法），写入 `symbol_map` 备注
- 全文统一替换，`rewrite_log` 记录 `change_type: terminology_unify`
- 无法确定标准译法的术语，保留并标记，报告中列出请作者确认
**披露**：术语选择有争议时披露

### E2-05 原文包含不宜发表的内容
**信号**：竞赛队号、指导教师致谢中的敏感信息、未授权的企业数据、
明显来自他处未标注引用的段落
**处理**：
- 竞赛痕迹（队号、赛题编号）→ 直接删除，`rewrite_log` 记录
- 疑似未标注引用的段落 → **STOP 并报告**，绝不静默改写掩盖
  （这可能是抄袭，必须让作者知道并处理）
- 企业数据 → 标记 `NEEDS_AUTHOR_REVIEW`，提示需确认数据使用授权
**披露**：必须

### E2-06 改写后触发 G2（检出幻觉）
**信号**：G2 任一 error 条件命中
**处理**：按 `quality-gates.yaml#G2.on_fail`：
- 第 1-2 次：重试，提示词中追加违规清单 + 强化约束
- 第 3 次：**block**。输出诊断报告，绝不带着幻觉内容继续
**披露**：必须

---

## S3 质量评估阶段

### E3-01 内容过少无法评估
**信号**：正文 < 1500 词，或缺 3 个以上必需语义角色
**处理**：
- `tier: insufficient-content`
- `confidence` 设为 0.3 以下
- `caveats` 说明"内容量不足以支撑 SCI 论文评估"
- 触发 G3 特殊分支 → 生成「内容补充指引报告」而非继续流水线
**披露**：必须

### E3-02 无法评估的维度
**信号**：如原文无代码/数据说明 → 无法评估 `reproducibility`
**处理**：
- 该维度给出基于现有信息的**保守**评分（缺信息 → 低分，不是不评）
- `justification` 明确写"因缺少 X 信息，本项按最低可验证水平评分"
- `caveats` 登记
**不允许**：因为无法评估就给中间分数（6分）蒙混

### E3-03 评分与分数带明显不符
**信号**：各维度分数与 `total_score` 算不上，或 `tier` 与分数矛盾
**处理**：自检环节（`self_check.score_arithmetic_verified`）必须重算一遍，
不符则修正后再输出。`score_breakdown` 必须写出可核验的算式。

---

## S4 期刊匹配阶段

### E4-01 网络不可用
**信号**：检索工具失败
**处理**：
- 仅用 `config/journals.yaml` 本地库匹配
- `self_check.offline_mode = true`
- 每个 `impact_factor.source` 标为 `"local-cache (seed data), UNVERIFIED"`，
  `note` 写"未联网核实，投稿前必须自行到 JCR/期刊官网复核"
- `data_sources` 全部标 `type: local-db`
**披露**：必须，报告中用醒目区块声明

### E4-02 候选不足 3 个
**信号**：G4-02 触发
**处理**：按 `strategies_order` 逐级放宽：
`exact_scope_match` → `broaden_to_secondary_field` → `broaden_to_application`
→ `include_lower_quartile`
全部用尽仍不足 → 降级：输出现有候选 + 人工检索建议
（Elsevier Journal Finder、Springer Journal Suggester、Web of Science 分类浏览）
**披露**：是

### E4-03 影响因子查不到
**信号**：检索无结果或结果冲突
**处理**：`impact_factor.value = null`，`note` 说明查询情况。
**绝不填估计值**——一个 null 比一个错的数字有用得多。
**披露**：是

### E4-04 疑似掠夺性期刊
**信号**：命中 `config/journals.yaml#predatory_signals` 任一项
**处理**：
- 移入 `excluded_candidates`，`excluded_by: predatory_risk`
- `reason` 写明命中的具体信号
- 若某期刊本已在推荐列表中才发现风险 → 移除并在报告中提醒作者警惕
**披露**：必须

### E4-05 期刊收录状态存疑
**信号**：`config/journals.yaml` 条目带 `flags: [requires_indexing_verification]`，
或检索发现该刊曾被 SCIE 剔除
**处理**：可以推荐，但必须在 `rejection_risks` 中列出
"收录状态需自行核实"并给出核实链接（Web of Science Master Journal List）
**披露**：必须

---

## S5 模板适配阶段

### E5-01 官方模板下载失败
**信号**：`fetch_template.py` 返回非 200 / 超时 / 页面结构变化
**处理**：走 `pipeline.yaml#S5.degrade_chain`：
1. 官方期刊模板
2. 出版商通用模板（`elsarticle` / `IEEEtran` / `sn-jnl`）
3. `assets/templates/{publisher}-generic/`
4. 标准 `article` 类

每降一级写一条 `degrade` 审计事件。
**披露**：必须。报告用固定措辞：
> 本稿使用「{方案名}」排版，非目标期刊官方模板。投稿前必须：
> 1) 从期刊官网下载官方模板；2) 迁移内容；3) 按 Guide for Authors 重新核对格式。

### E5-02 模板要求的字段原文没有
**信号**：模板需要 ORCID、通讯作者、机构地址、CRediT 贡献声明等，IR 中为 null
**处理**：保留模板占位（如 `\orcid{}`），在 `unmapped.json` 登记，
报告的「待补清单」列出。**不许编造机构名或邮箱。**
**披露**：是

### E5-03 内容超出期刊长度限制
**信号**：`constraints.max_pages` / `max_words` 超标
**处理**：
- **不自动删内容**
- 生成压缩建议：哪些章节可精简、哪些内容可移入附录/补充材料、
  哪些图可合并，附各方案的预估节省量
- `flags: [NEEDS_AUTHOR_REVIEW]`，交作者决策
- 例外：明确的冗余（重复表述、竞赛残留）可自动删并记录
**披露**：是

### E5-04 双栏排版导致公式溢出
**信号**：IEEE 等双栏模板 + 长公式
**处理**：
- 优先尝试 `\begin{split}` / `multline` 拆行（不改语义）
- 仍溢出 → 建议改为跨栏浮动（`figure*` 风格的 `strip` 环境）或移入附录
- 标记具体公式 id，报告中列出
**披露**：是

### E5-05 图片格式不符要求
**信号**：期刊要求矢量图/300dpi，原图是低分辨率位图
**处理**：
- **不做插值放大**（假的高分辨率比低分辨率更糟）
- `gaps` 登记 `category: missing_figure_source`，`how_to_fix` 写明期刊要求
- 报告中逐图列出当前规格与要求规格
**披露**：必须

---

## S6 多轮校验阶段

### E6-01 LaTeX 工具链不可用
**信号**：`latexmk` / `pdflatex` 探测失败
**处理**：
- `latex_compile_check` 状态设 `skipped`，`skip_reason` 说明
- G6-07 按 `skippable_when: latex_toolchain_unavailable` 跳过 → `degrade`
- 其余检查器正常执行
- 不产出 PDF
**披露**：必须，报告声明"成稿未经 LaTeX 编译验证，请自行编译确认"

### E6-02 修复引入新错误（震荡）
**信号**：同一 `finding.id` 连续两轮出现，或 error 总数不下降
**处理**：
- 触发 `escalate_if_oscillating`
- 停止对该项的自动修复
- 标记 `requires_author: true`，写明震荡情况与两种修法的冲突点
- 继续处理其他项
**披露**：是

### E6-03 达到轮次上限仍有 error
**信号**：round == 4 且 `error_count > 0`
**处理**：
- `verdict: FAIL_BLOCKED`
- 成稿状态标 `DRAFT_WITH_BLOCKERS`
- 仍然交付文件（作者可手工修完再投）
- 报告首页顶部用醒目区块列出每个残留 error 的位置、原因、建议修法
- **绝不声称"已完成"或"零错误"**
**披露**：必须

### E6-04 数值一致性检出差异
**信号**：`cross_validation.numeric_consistency.mismatches` 非空
**处理**：这是**最高优先级 error**。
- 不自动"修复"（不知道哪个是对的）
- 逐条列出：位置、原始值、当前值
- `requires_author: true`
- G6 直接判 fail
**披露**：必须，且应在报告中置顶

### E6-05 占位符残留
**信号**：成稿中检出 `[[MISSING]]` / `[[UNVERIFIED_REF]]` / `TODO`
**处理**：
- 正确处理方式：**删除依赖该占位符的完整断言**（整句或整段），
  内容保留在 `gaps` 清单中交作者补
- 不是把占位符替换成看起来合理的内容
- 删除操作记入 `rewrite_log`，`risk: medium`，报告中列出被删内容
**披露**：必须

---

## S7 结果汇报阶段

### E7-01 上游产物缺失
**信号**：某阶段输出文件不存在
**处理**：报告对应章节写"该阶段未执行/失败"，说明原因与影响，
不留空白也不编造内容
**披露**：是

### E7-02 报告内容与审计日志矛盾
**信号**：`audit.jsonl` 有 `degrade` 事件但报告未提及
**处理**：以审计日志为准，补入报告。
这是**报告生成的自检项**：`build_report.py` 会比对 `audit.jsonl` 中所有
`degrade` / `auto_fix` 事件是否都在报告中出现。
**披露**：必然

---

## 全局异常

### EG-01 重试预算耗尽
**信号**：`max_total_retries` (12) 达到
**处理**：`block`。生成部分完成报告：已完成阶段、卡住位置、
已产出的可用工件、建议的人工介入点。

### EG-02 用户中断
**信号**：SIGINT / 进程终止
**处理**：原子写机制保证无半成品文件。已完成阶段的产物完整可用，
`--stage S<n>` 可续跑。审计日志记录中断点。

### EG-03 磁盘写入失败
**信号**：`OSError` on write
**处理**：立即停止，保留已有产物，报告失败位置。不重试（大概率是空间或权限问题）。

### EG-04 用户要求跳过质量门控
**信号**：用户说"别检查了直接给我"、"不用管格式"
**处理**：
- G1/G3/G4/G5 → 可以按用户要求放宽，但报告中声明"按用户要求跳过 X 检查"
- **G2/G6 不可跳过**。这两个涉及学术诚信（幻觉内容）与投稿有效性（零错误）。
  解释原因，提供替代方案（如"我可以先给你当前版本，同时列出未解决的问题"），
  但不静默关闭检查。
