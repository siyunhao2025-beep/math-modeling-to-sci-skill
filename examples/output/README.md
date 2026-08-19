# 示例输出（examples/output）

本目录说明一次成功运行后 `runs/<workdir>/` 下应产出的文件。
真实示例可由以下命令生成（需先安装依赖，见 `requirements.txt`）：

```bash
export PYTHONPATH="$PWD/scripts"
python scripts/run_pipeline.py \
  --input examples/input/sample-modeling-report.tex \
  --workdir runs/demo \
  --scope-tags applied-mathematics,mathematical-modelling,optimization \
  --method-tags ode-pde,numerical-simulation,optimization \
  --score 7.2
```

## 预期产物

| 路径 | 说明 |
|------|------|
| `01-parse/manuscript.ir.json` | S1 解析出的中间表示（IR） |
| `02-rewrite/manuscript.rewritten.json` | S2 改写稿（CLI demo 为直通占位） |
| `03-assess/assessment.json` | S3 六维评分（CLI demo 为占位） |
| `04-journals/journal-match.json` | S4 期刊推荐（符合 `journal-match.schema.json`） |
| `05-template/build/main.tex` | S5 重组后的 LaTeX 骨架 |
| `05-template/build/references.bib` | S5 生成的参考文献 |
| `05-template/MANIFEST.json` | S5 模板级别与章节映射 |
| `06-validate/validation-final.json` | S6 校验结果与状态标签 |
| `conversion-report.md` | S7 汇总报告 |

## 状态标签

- `SUBMISSION_READY`：G6 校验零错误。
- `DRAFT_WITH_BLOCKERS`：仍有 error，报告首页列出待修项。

> 注意：CLI demo 用 `--ai-stub` 直通 S2/S3，仅供流程跑通演示；
> 真实学术改写与评估由 Skill 提示词（prompts/02、prompts/03）执行。
