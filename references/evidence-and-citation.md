# 证据账本与引用双检

## 1. 统一证据层级

对每个核心主张标记来源状态：

`PROJECT_RESULT` → `SOURCE_CONFIRMED` → `VERIFIED_EXTERNAL` → `USER_CONFIRMED` → `INFERRED` / `SUGGESTED` → `MISSING`

层级描述来源，不自动等同于可信度。一个项目结果若运行设计错误，仍不能支持主张；一个外部文献若范围不匹配，也不能支撑当前句子。

每条 claim 至少记录：

- `claim_id`、原句、章节位置；
- claim type：descriptive、comparative、quantitative、causal、mechanistic；
- 数据/代码/图表/公式/文献证据 ID；
- 条件、范围和排除项；
- status：SUPPORTED、PARTIAL、UNSUPPORTED、CONTRADICTED、PENDING；
- `verification.required_depth`、`verification.reached_depth`、`verification.checked_at` 与
  `verification.evidence_locator`；
- 作者动作与最后核验时间。

主张验证深度使用一条累积式工作流阶梯：

| 深度 | 至少证明了什么 | 典型定位 |
|---|---|---|
| `text_bound` | 已检查当前主张文字、限定词和上下文 | 稿件章节、claim map 条目 |
| `source_bound` | 已回到支撑该主张的具体来源或项目证据 | 页/图/表、数据单元、公式或证据卡 |
| `execution_bound` | 已复核产生该结果的运行或计算记录 | 运行 ID、日志、脚本版本和结果文件 |
| `render_bound` | 已在最终交付形态中复核呈现与回链 | 当前成品哈希、页码/图号和审阅记录 |

`required_depth` 由主张类型和风险决定；`reached_depth` 只能填写实际完成且包含前序步骤的最深层级。
`text_bound` 用于记录尚未回到证据的中间状态，不能作为 Gate G 最终主张的最低要求；Gate G 至少
要求 `source_bound`。两字段还必须使用上述枚举值、`reached_depth` 不低于 `required_depth`，并记录
核验时间与可解析的证据定位。该契约只验证声明是否完整、层级是否匹配，不会替代科学判断，也不
自动证明定位内容真实。
若无法提供相应证据，应降低 `reached_depth`、收窄主张或保持阻塞，不得用更深的标签代替核验。

## 2. 引用身份核验

只允许四态：

| 状态 | 含义 | 处置 |
|---|---|---|
| `VERIFIED` | 标题、作者、年份、来源、DOI/标识与权威记录一致 | 可进入支持核验 |
| `MISMATCH` | 文献存在但元数据冲突 | 修正后重验 |
| `UNRESOLVED` | 无法证明记录身份 | 不进入最终论证链 |
| `RETRACTED` | 兼容旧账本的撤稿简写 | 阻断；新账本同时填写独立的出版完整性状态 |

优先核对版本记录页和出版社页面，再用独立元数据源交叉检查。DOI 可解析只能证明标识存在，不能证明正文支持当前句子。

## 3. 出版完整性核验

身份字段回答“是不是这篇文献”，出版完整性字段回答“这篇文献后来是否出现正式通知”。即使
DOI、标题、作者和年份全部一致，也必须另填 `integrity_status`：

| 状态 | 含义 | Gate G 处置 |
|---|---|---|
| `NO_SIGNAL_FOUND` | 在记录的来源与时间没有发现完整性信号 | 可继续；不等于证明记录干净 |
| `RETRACTED` | 出版方已撤稿 | 阻断作为支持证据 |
| `WITHDRAWN` | 出版方已撤回 | 阻断作为支持证据 |
| `REMOVED` | 出版方已移除或以移除通知替代 | 阻断作为支持证据 |
| `EXPRESSION_OF_CONCERN` | 出版方发布关注声明 | 阻断，转作者判断 |
| `CORRECTED` | 存在 correction、corrigendum 或 erratum | 继续判断更正是否影响当前引用 |
| `NOT_CHECKED` | 尚未完成检查 | 阻断，转作者处理 |

每个非 `NOT_CHECKED` 记录都要提供 `integrity_source_url` 和带时区的
`integrity_checked_at`；Gate G 只接受 HTTPS 来源。优先查看出版社文章页和正式通知，第三方索引
可用于发现线索，但索引没有返回信号只能写 `NO_SIGNAL_FOUND`。

`correction_effect` 必须显式填写。非 `CORRECTED` 记录使用 `NOT_APPLICABLE`；`CORRECTED`
记录使用以下三态：

- `UNAFFECTED`：更正不影响当前引用内容；同时用 `correction_locator` 链接 HTTPS 正式更正通知；
- `AFFECTS_CITED_CONTENT`：更正改变当前引用的数值、方法或结论，阻断原支持关系并重做核验；
- `UNKNOWN`：尚不能判断影响，保持作者处理状态，不默认通过。

`scripts/forge.py` 只校验账本的状态、来源、时间和更正处置，不联网查询，也不证明来源页面内容
真实、完整或最新。出版完整性是引用身份/支持双检之外的独立安全轴，不替代其中任一检查。

## 4. 句子支持核验

| 状态 | 含义 | 处置 |
|---|---|---|
| `SUPPORTS` | 对象、条件、范围和强度直接匹配 | 可保留 |
| `PARTIALLY_SUPPORTS` | 只支持部分范围或较弱结论 | 收窄句子 |
| `BACKGROUND_ONLY` | 只适合作背景 | 不作为核心证据 |
| `CONTRADICTS` | 与句子相反 | 阻塞，修改或移除 |
| `DOES_NOT_SUPPORT` | 文献讨论的不是这件事 | 阻塞，替换或移除 |
| `CANNOT_VERIFY` | 访问深度不足 | 获取合法全文或降级句子 |

支持核验逐项比较对象、时间/空间/样本范围、条件、方法类型、基线定义和结论强度。题名关键词重叠不构成支持。

## 5. 句子强度与访问深度

这里的 `access_level` 描述外部文献读到了多深；上面的主张验证深度描述整条论证链核验到了哪一层。
二者相互补充但不能互相代替：读到全文不等于已经复跑项目结果，完成运行也不等于外部引用支持句子。

| 句子层级 | 最低访问深度 | 定位要求 |
|---|---|---|
| background | metadata_only | 通常不需要页码 |
| method/existence | abstract_only | 只描述文献明确的方法/存在性 |
| quantitative | full_text | 页、图或表 |
| causal/mechanistic | full_text | 页、图或表，并核对原文语气 |

项目自身结果可用 `project_result`，但必须链接运行 ID、结果文件和图表/表格位置。

访问深度不足时只有两条出路：合法获取更深证据，或把句子降级到现有证据能支撑的范围。不要用“据报道”“大约”伪装完成核验。

## 6. 高风险错配

- 综述冒充原始实验；
- 关联证据支撑因果；
- 模拟/再分析写成观测；
- 不同人群、区域、时段或条件相互替代；
- 用二手来源给精确数字；
- 引用方向与原文结论相反；
- 用模型训练数据支撑泛化；
- 用期刊样例论文替代官方作者指南。

任何一项命中时，至少标为 blocker 或 `AUTHOR_ACTION_REQUIRED`。

## 7. 待确认格式

统一写为：

```text
待确认：<需要确认的事实或主张>。
已核查：<来源、日期、可访问深度>。
阻塞原因：<缺全文、元数据冲突、项目结果缺失等>。
下一步：<获取何种材料或如何收窄句子>。
```

`待确认` 不得进入摘要、结论和贡献声明的确定性论证链。
