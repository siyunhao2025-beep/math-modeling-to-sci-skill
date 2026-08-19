# 公共 IO 契约

> 所有阶段共享的输入输出约定。违反契约会导致下游阶段无法消费。

## 一、通用输出规则

### 文件写入
- 路径：`{workdir}/{stage_dir}/{filename}`，`stage_dir` 见 `config/pipeline.yaml`
- 编码：UTF-8 无 BOM
- 换行：`\n`（LF），不用 CRLF
- JSON：2 空格缩进，`ensure_ascii=false`（保留中文原文可读），key 顺序与 schema 一致
- 原子写：先写 `{filename}.tmp`，校验通过后 `os.replace()` 重命名

### JSON 输出的硬性要求
1. **必须先过 schema 校验再交付**。校验命令：
   ```bash
   python scripts/validate/validate_ir.py --ir <file> --schema config/schema/<name>.schema.json
   ```
2. 不输出 schema 未定义的字段（所有 schema 都设了 `additionalProperties: false`）
3. `null` 与缺省语义不同：schema 允许 `null` 的字段，"不知道"填 `null`，不要省略
4. 不输出被 Markdown 代码块包裹的 JSON——直接写文件，不要写进对话

### ID 命名规则（跨阶段稳定，不许重编号）

| 对象 | 格式 | 示例 |
|------|------|------|
| section | `sec-{序号}` 或 `sec-{层级路径}` | `sec-3`、`sec-3.2` |
| block | `blk-{序号}` | `blk-142` |
| equation | `eq-{序号}` | `eq-7` |
| figure | `fig-{序号}` | `fig-2` |
| table | `tab-{序号}` | `tab-1` |
| reference key | `{firstauthor}{year}{firstword}` 全小写 | `zhang2023optimal` |
| gap | `gap-{序号}` | `gap-5` |
| improvement action | `act-{序号}` | `act-3` |
| validation finding | `{CHECKER}-{序号}` | `CITE-001`、`FIG-003` |

**S1 分配的 id 在后续阶段必须保持不变**。S2 新增内容用新序号（从最大值+1 继续），
删除内容不回收 id（保留空洞，便于追溯）。

## 二、占位符标记规范

三种标记，语义严格区分：

### `[[MISSING: 说明]]`
原文缺少必要内容，需作者补充。

```
The proposed model was validated on [[MISSING: 验证数据集名称与规模，
原文仅提到"实际数据"未说明来源]].
```

必须同时在 `gaps` 登记。G6 硬门控要求成稿中不得残留此标记——
处理方式是**删除依赖该缺失内容的断言**，而非填空。

### `[[UNVERIFIED_REF: 描述]]`
需要引用但无法验证到真实文献。

```
Similar approaches have been applied in supply chain contexts
[[UNVERIFIED_REF: 需要一篇 2020 年后的绿色供应链多目标优化文献]].
```

不写入 `references` 数组。成稿前必须删除该断言或由作者补真实引用。

### `flags: [NEEDS_AUTHOR_REVIEW]`
内容存在但你对其正确性/适当性有疑虑，需作者确认。

不阻塞流程，但必须列入报告的「需作者复核」清单。

> 三者的共同点：**宁可留白并说明，不可填充并隐瞒**。

## 三、各阶段 IO 速查

| 阶段 | 主要输入 | 主要输出 | Schema |
|------|---------|---------|--------|
| S1 | `00-input/*` | `01-parse/manuscript.ir.json`<br>`01-parse/parse-warnings.json` | `manuscript.schema.json` |
| S2 | `01-parse/manuscript.ir.json`<br>`03-assess/assessment.json`（回退时） | `02-rewrite/manuscript.rewritten.json`<br>`02-rewrite/references.bib`<br>`02-rewrite/rewrite-diff.md` | `manuscript.schema.json` |
| S3 | `02-rewrite/manuscript.rewritten.json` | `03-assess/assessment.json` | `assessment.schema.json` |
| S4 | `03-assess/assessment.json`<br>`02-rewrite/manuscript.rewritten.json`<br>`config/journals.yaml` | `04-journals/journal-match.json`<br>`04-journals/journal-evidence/*` | `journal-match.schema.json` |
| S5 | `02-rewrite/manuscript.rewritten.json`<br>`04-journals/journal-match.json` | `05-template/template/*`<br>`05-template/build/main.tex`<br>`05-template/build/references.bib`<br>`05-template/unmapped.json` | — |
| S6 | `05-template/build/*`<br>`01-parse/manuscript.ir.json`（数值基准） | `06-validate/validation-round-{n}.json`<br>`06-validate/validation-final.json` | `validation.schema.json` |
| S7 | 全部工件 + `audit.jsonl` | `07-report/conversion-report.md`<br>`07-report/manuscript-final.*` | — |

## 四、阶段衔接的强制约束

### S1 → S2：不许丢东西
S2 输出的 IR 必须保留：
- `equations` / `figures` / `tables` 的**全部条目**（数量不得减少）
- `symbol_map` 的全部 key（可增不可删）
- `provenance.source_sha256`（链式追溯）
- `gaps` 的全部条目（可增，删除仅当该 gap 已被真实解决）

删除某个数学对象的意图 → 改为在 `gaps` 登记 `NEEDS_AUTHOR_REVIEW`，说明建议删除的理由。

### S2 → S3：保证评估独立性
S3 **只读** `manuscript.rewritten.json` 本身，**不读** `rewrite_log`、不读 S2 的自述理由。

理由：如果 S3 看到 S2 说"我已强化了创新点论述"，会倾向于确认这个说法，
形成自我确认偏误。S3 必须像一个第一次看到这篇稿子的审稿人。

### S3 → S4：分数决定档位
S4 必须依据 `assessment.total_score` 与 `assessment.tier` 选择期刊档位，
参照 `config/journals.yaml` 的 `matching.quality_bands`。

不许无视分数推荐顶刊（对作者是浪费时间），也不许因为分数低就只推荐水刊
（应说明"补充 X 后可冲刺 Y 刊"）。

### S4 → S5：约束必须落地
`recommendations[0].constraints` 中的每一项（字数、页数、摘要长度、引用格式）
都必须在 S5 生成成稿时实际应用，并在 S6 被 `check_journal_constraints` 验证。

### S5 → S6：提供校验基准
S6 需要三个基准：
1. `05-template/build/` — 被校验对象
2. `04-journals/journal-match.json#constraints` — 格式要求
3. `01-parse/manuscript.ir.json` — **数值一致性的原始基准**（注意是 S1 的，不是 S2 的）

### S6 → S7：诚实传递状态
`validation-final.json` 的 `verdict` 决定报告的状态标签：

| verdict | 报告状态标签 | 含义 |
|---------|-------------|------|
| `PASS` | `SUBMISSION_READY` | 零 error，可投稿 |
| `PASS_WITH_WARNINGS` | `SUBMISSION_READY_WITH_NOTES` | 零 error，有建议改进项 |
| `FAIL_RETRY` | — | 内部状态，不应到 S7 |
| `FAIL_BLOCKED` | `DRAFT_WITH_BLOCKERS` | 有残留 error，**不得称可投稿** |

S7 不得美化 `FAIL_BLOCKED` 的表述。

## 五、审计日志写入契约

每个阶段至少写入：
- `stage_start`（含输入文件哈希）
- `stage_end`（含输出文件哈希、耗时）
- `gate_decision`（若有门控）

按需写入：`auto_fix`、`degrade`、`external_call`、`error`、`human_input`

格式见 `config/schema/audit-log.schema.json`。写入方式：

```python
from scripts.audit.logger import AuditLogger
log = AuditLogger(workdir, run_id)
log.stage_start("S2", inputs=[...])
log.external_call("S2", kind="doi_lookup", query="10.1016/j.apm.2023.01.001",
                  status="200", evidence_file="evidence/doi-001.json")
log.degrade("S5", frm="official_journal_template", to="bundled_skeleton",
            cause="下载超时", impact="格式需人工复核")
log.stage_end("S2", outputs=[...], duration_ms=42000)
```

**审计日志是 append-only**。永远不要重写或删除已有行。
