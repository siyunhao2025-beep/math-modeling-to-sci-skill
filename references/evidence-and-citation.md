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
- 作者动作与最后核验时间。

## 2. 引用身份核验

只允许四态：

| 状态 | 含义 | 处置 |
|---|---|---|
| `VERIFIED` | 标题、作者、年份、来源、DOI/标识与权威记录一致 | 可进入支持核验 |
| `MISMATCH` | 文献存在但元数据冲突 | 修正后重验 |
| `UNRESOLVED` | 无法证明记录身份 | 不进入最终论证链 |
| `RETRACTED` | 已撤稿/失效 | 不作为支持证据 |

优先核对版本记录页和出版社页面，再用独立元数据源交叉检查。DOI 可解析只能证明标识存在，不能证明正文支持当前句子。

## 3. 句子支持核验

| 状态 | 含义 | 处置 |
|---|---|---|
| `SUPPORTS` | 对象、条件、范围和强度直接匹配 | 可保留 |
| `PARTIALLY_SUPPORTS` | 只支持部分范围或较弱结论 | 收窄句子 |
| `BACKGROUND_ONLY` | 只适合作背景 | 不作为核心证据 |
| `CONTRADICTS` | 与句子相反 | 阻塞，修改或移除 |
| `DOES_NOT_SUPPORT` | 文献讨论的不是这件事 | 阻塞，替换或移除 |
| `CANNOT_VERIFY` | 访问深度不足 | 获取合法全文或降级句子 |

支持核验逐项比较对象、时间/空间/样本范围、条件、方法类型、基线定义和结论强度。题名关键词重叠不构成支持。

## 4. 句子强度与访问深度

| 句子层级 | 最低访问深度 | 定位要求 |
|---|---|---|
| background | metadata_only | 通常不需要页码 |
| method/existence | abstract_only | 只描述文献明确的方法/存在性 |
| quantitative | full_text | 页、图或表 |
| causal/mechanistic | full_text | 页、图或表，并核对原文语气 |

项目自身结果可用 `project_result`，但必须链接运行 ID、结果文件和图表/表格位置。

访问深度不足时只有两条出路：合法获取更深证据，或把句子降级到现有证据能支撑的范围。不要用“据报道”“大约”伪装完成核验。

## 5. 高风险错配

- 综述冒充原始实验；
- 关联证据支撑因果；
- 模拟/再分析写成观测；
- 不同人群、区域、时段或条件相互替代；
- 用二手来源给精确数字；
- 引用方向与原文结论相反；
- 用模型训练数据支撑泛化；
- 用期刊样例论文替代官方作者指南。

任何一项命中时，至少标为 blocker 或 `AUTHOR_ACTION_REQUIRED`。

## 6. 待确认格式

统一写为：

```text
待确认：<需要确认的事实或主张>。
已核查：<来源、日期、可访问深度>。
阻塞原因：<缺全文、元数据冲突、项目结果缺失等>。
下一步：<获取何种材料或如何收窄句子>。
```

`待确认` 不得进入摘要、结论和贡献声明的确定性论证链。
