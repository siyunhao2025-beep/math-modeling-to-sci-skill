# 图表契约：按证据覆盖，而非按数量凑图

## 1. 先问每张图证明什么

为每个顶层 Figure 或 Table 建立契约：

| 字段 | 要求 |
|---|---|
| ID | 稳定且唯一 |
| scientific_question | 这张图回答的唯一科学问题 |
| claim_ids | 支持的正文主张 |
| evidence_role | 机制、主结果、比较、验证、不确定性、边界等 |
| source_data | 真实源数据/结果文件 |
| script | 可重建图的脚本或明确生成流程 |
| outputs | 已交付并实际审阅的当前图件文件；至少一个，路径相对工作区 |
| target_width_mm | 图件在稿件或投稿版式中的目标物理宽度，正数，单位 mm |
| figure_type | 可选；`data`、`roadmap` 或 `schematic`。旧清单省略时保持兼容；声明后启用对应检查 |
| editable_artifact | `roadmap`/`schematic` 的可编辑源、格式与稳定语义对象清单；见下节 |
| panels | 每个面板提供的不同证据 |
| caption_claim | 图注可核验结论与边界 |
| risks | 可能误导的轴、截断、平滑、尺度、配色 |
| visual_review | 审阅者、带时区时间、按目标物理宽度审阅时的 `reviewed_width_mm`，以及每个 `outputs` 文件在审阅时的 SHA-256 |

没有独立科学问题或证据增量的图不进入正式稿。同一数据换成折线、柱状和雷达图不算三项证据。

### 可编辑路线图/示意图的语义对象契约

路线图或原理示意图若声明 `figure_type`，建议同时提供 `editable_artifact`：

```json
{
  "figure_type": "schematic",
  "editable_artifact": {
    "source": "04-manuscript/fig-method.svg",
    "format": "svg",
    "objects": [
      {"object_id": "input-data", "kind": "node"},
      {"object_id": "model", "kind": "node"},
      {"object_id": "input-to-model", "kind": "connector",
       "source_id": "input-data", "target_id": "model"}
    ],
    "content_ledger": {
      "source_object_ids": ["raw-input", "cleaning", "model", "input-to-model"],
      "entries": [
        {"source_id": "raw-input", "action": "merged", "target_id": "input-data",
         "reason": "Acquisition and cleaning share one role in the overview."},
        {"source_id": "cleaning", "action": "merged", "target_id": "input-data",
         "reason": "Acquisition and cleaning share one role in the overview."},
        {"source_id": "model", "action": "retained", "target_id": "model"},
        {"source_id": "input-to-model", "action": "retained",
         "target_id": "input-to-model"}
      ]
    }
  }
}
```

`format` 只接受 `svg`、`drawio`、`pptx`，源文件必须位于工作区内且真实存在。`object_id`
在同一图中必须唯一并跨修订保持稳定；连接对象的 `source_id`、`target_id` 必须指向清单中的
对象。局部修订只改目标对象及必要连线，未涉及对象保留原 ID。该契约验证可编辑源与引用完整性，
不判断布局、美观、连线语义或科学内容是否正确。为兼容旧工作区，缺少 `figure_type` 不阻断；
已声明路线图/示意图但缺 `editable_artifact` 时给出警告。

当路线图或示意图从更细的蓝图、旧版图或对象清单压缩而来时，用 `content_ledger` 防止
“画面变简洁”被误当成可以静默丢对象：`source_object_ids` 登记压缩前对象，每个对象在
`entries` 中恰好出现一次，`action` 只能是 `retained`、`merged` 或 `omitted`。前两种必须
指向当前 `objects` 中的 `target_id`；`merged` 和 `omitted` 必须写理由。省略对象还要明确
布尔值 `evidence_bearing`；若它承载证据，只有 `author_approved=true` 才能通过。旧清单缺少
`content_ledger` 时只给警告；一旦提供，未知目标、重复处置、未处置对象和未经批准的证据省略
都会阻断 Gate G。该账本记录对象去向，不要求把所有内容塞进一张图，也不替代人工判断一项省略
是否科学合理。

## 2. 常见证据角色

- 研究/方法路线图：仅在复杂流程确实需要总览时使用；不是每篇论文强制图 1。
- 数据与质量审计：分布、缺失、偏差、覆盖范围。
- 模型/机制示意：明确标为 conceptual schematic，不能冒充观测。
- 主结果：直接回答研究问题。
- 公平比较：基线、主模型和成本/风险并列展示。
- 验证：残差、外部验证、精确解、交叉验证等。
- 不确定性：置信区间、参数/情景传播、稳定性。
- 边界与失败：模型失效区、负结果或敏感条件。

缺少某角色不自动失败；是否需要由 claim map 和模型原型决定。

## 3. 图、表或正文的选择

- 精确数值、参数、样本量和多指标对照优先表；
- 趋势、分布、空间结构、关系与不确定性优先图；
- 一两个关键数值直接写正文；
- 重复信息不同时出现在图和表，除非两者分别承担趋势与精确查值。

## 4. 科学与视觉检查

每张图检查：

- 轴名、单位、尺度、零点、方向与数据一致；
- 误差条/置信带含义和样本单位明确；
- 统计显著性与效应大小不混淆；
- 过滤、平滑、插值、截轴和归一化被披露；
- 不使用颜色作为唯一编码；使用线型、点型、纹理或直接标签冗余编码；
- 色盲友好且黑白打印仍可区分；
- 矢量优先，位图满足目标期刊分辨率；
- caption 独立可读，说明对象、条件、指标、结论和边界；
- 正文明确引用并解释，不把图扔给读者自己猜。

脚本只能检查文件、字段、尺寸和链路；图是否科学、是否误导必须逐张人工/视觉复核。先按稿件
实际栏宽或目标投稿版式填写正数 `target_width_mm`，再把最终输出缩放到该物理宽度逐张审阅；
复核记录除 `reviewer` 与 `reviewed_at` 外，还必须填写相同的 `reviewed_width_mm`，并在
`output_sha256` 中按相对路径记录每个当前输出文件的 lowercase SHA-256。两种宽度相差超过
0.1 mm 会被 Gate G 阻断。任何重新渲染、后期标注、压缩、替换或目标排版宽度变化都会使旧
复核失效；必须按新的最终尺寸重新打开文件、逐张检查并更新记录，不能把旧签名沿用到新图。

## 5. 数量与变更

不要预设“标准论文必须 N 张图”。建议数量来自未覆盖的关键 claim，而非历史平均或营销效果。

新增图时必须新增至少一种：独立分析、实验、证据角色或决策问题。删除图时检查其 claim 是否仍被表格、正文或其他图充分覆盖。

结果、模型或研究问题变化后，相关图、图注、正文、摘要和结论一并失效。按 `references/change-control.md` 回退。
