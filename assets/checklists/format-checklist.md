# 格式校验清单（format-checklist）

> 供 S6 多轮校验逐项核对。每个勾选项对应一个检查器，详见 `scripts/validate.py`。

## 结构（validate_ir / check_journal_constraints）
- [ ] IR 通过 `manuscript.schema.json` 校验
- [ ] 摘要字数 ≤ `abstract_max_words`
- [ ] 关键词数量 ≤ `max_keywords`
- [ ] 全文总字数 ≤ `max_words`（若设上限）
- [ ] 参考文献样式 = `reference_style`

## 引用（check_citations / cross_validate）
- [ ] 正文 `\cite{key}` 均在 `references.bib` 中存在（cited_not_in_bib = []）
- [ ] `references.bib` 条目均被引用（in_bib_not_cited = []）
- [ ] 无 `[[UNVERIFIED_REF]]` 残留

## 图表（check_figures_tables）
- [ ] 无孤儿图（每个 figure 至少被一处引用）
- [ ] 无孤儿表（每个 table 至少被一处引用）
- [ ] 图/表 caption 完整
- [ ] 图源文件存在或可生成（缺失已登记 gap）

## 公式（check_equations）
- [ ] 公式编号与正文 `\ref` 对应
- [ ] 公式内容与 IR `equations[].latex` 一致（语义/数值零改动）
- [ ] 无孤立公式（未被引用至少警告）

## 语言（check_language / check_cjk_residue）
- [ ] 目标语言 en 时零 CJK 残留（正文 + caption + 外文标题）
- [ ] 无禁止占位符：`[[MISSING]]` / `TODO` / `TBD` / `XXX` / `\ref{??}` / `??`
- [ ] 时态/语态/禁用词符合 `config/style-rules.yaml`

## 编译（latex_compile_check，可跳过）
- [ ] 有工具链时 `pdflatex`/`latexmk` 编译通过
- [ ] 无工具链时标记 degrade 并在报告声明
