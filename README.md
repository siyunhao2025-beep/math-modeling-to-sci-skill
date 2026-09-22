# M²SCI Forge

> **不把建模报告翻译成英文；把模型证据锻造成经得起审稿的 SCI 论文。**

![M²SCI Forge：从模型证据到期刊论文](assets/brand/m2sci-forge-hero.png)

从题解到论证，从结果到证据，从成稿到投稿前审查。

`math-modeling-to-sci` 面向已有数学建模报告、竞赛论文、技术建模文档和可复现实验工程。它不靠“SCI 腔”掩盖研究缺口，而是把原始事实、研究问题、再验证、论证链和期刊适配拆成可审计的工件。

支持 Word、LaTeX、LaTeX 工程与 Markdown；保留原有 S1–S8 运行时，并以新的 **FORGE × TRACE** 体系统一调度。

---

## 为什么普通“润色”不够

数学建模报告围绕“把题做出来”；SCI 论文必须回答另一组问题：

- 这是不是一个离开竞赛题面仍成立的研究问题？
- 贡献相对已有工作新增了什么，而不只是换了算法名？
- 结果是否有公平基线、稳健性、不确定性和外部边界？
- 每个数字、图表、公式和引用能否回到真实来源？
- 目标期刊的范围、体裁与当前规范是否真的匹配？

如果这些问题没有答案，英文再像论文，也只是“更像 SCI 的竞赛报告”。

---

## FORGE：五次锻造

```text
Fidelity     冻结事实与原始资产
    ↓
Opportunity  重构研究问题、缺口与贡献上限
    ↓
Revalidation 按模型原型补基线、稳健性与不确定性
    ↓
Grounding    建立主张—证据—图表—引用—章节闭环
    ↓
Editorial    用当前官方证据完成期刊匹配与投稿前审查
```

每个阶段同时通过 TRACE 五条质量轨：

| T | R | A | C | E |
|---|---|---|---|---|
| Traceability 可追溯 | Rigor 严谨性 | Argument 论证 | Compliance 合规 | Evidence 证据 |

任何关键 blocker 都不能被高总分抵消。

---

## 三个真正不同的设计

### 1. 零静默损失，而不是零删减

原稿所有图、表、公式、数字和结论都会进入资产账本；但无关竞赛内容不会被强塞进期刊正文。每项内容必须明确 `保留 / 改写 / 补充材料 / 删除 / 待定`，实质删除需要作者确认。

### 2. 引用过两道关

先证明“这篇文献真的存在、元数据正确”，再证明“它在相同对象、条件和范围下支持这句话”。DOI 能打开，不等于引用成立；只有摘要，也不能支撑精确数字或机制因果。

### 3. 验证跟着模型走

优化、评价、预测、分类、机理、信号、空间图网络和随机仿真使用不同验证菜单。不会对所有模型机械要求同一套交叉验证、消融或显著性检验，也不会为凑图表数量制造装饰性证据。

---

## 它会主动拒绝什么

- 只有方案、没有真实运行结果，却要求直接生成论文；
- 缺失数据、样本量、显著性或伦理编号由 AI “补齐”；
- 用算法复杂度包装创新，用语言润色包装研究升级；
- 把相关写成因果，把模拟写成观测，把计划写成已完成；
- 把本地期刊 seed 当作当前 IF、分区、APC 或作者指南；
- 输出“录用率”“必中期刊”或“保证录用”。

这不是保守，而是避免把最容易被编辑秒拒的问题留到最后。

---

## 最快开始

把 skill 放入 Codex skill 目录，上传 `.docx`、`.tex`、LaTeX `.zip` 或项目文件，然后说：

```text
使用 $math-modeling-to-sci。先不要改正文，完整盘点我的建模报告，
判断它是否值得转 SCI，并给出最小补强路线。
```

如果希望执行完整流程：

```text
使用 $math-modeling-to-sci。按 FORGE 全流程执行；遇到真正需要作者裁决、
缺关键证据或需要对外操作时再暂停。
```

### 可追溯工作区

```bash
python scripts/forge.py init runs/my-paper --input report.docx --route full
python scripts/forge.py status runs/my-paper
python scripts/forge.py gate runs/my-paper F
```

`init` 只建立快照、哈希和空白工件，不会伪造论文。`status` 检查确定性契约，不会把 schema 通过冒充科学有效。

### 旧流程兼容

```bash
python scripts/run_pipeline.py --input examples/input/sample-modeling-report.tex \
  --workdir runs/legacy-demo --mode dry-run --readiness auto
python scripts/readiness/run_readiness.py --workdir runs/legacy-demo
```

FORGE 与旧 S1–S8 的映射见 [`references/legacy-stage-map.md`](references/legacy-stage-map.md)。

---

## 你会拿到什么

完整路线通常产生：

- 原始材料快照、资产清单、内容处置账本和符号表；
- 研究问题—缺口—方法—证据—贡献—边界定位；
- 主/辅模型画像与按原型生成的再验证计划；
- 基线、公平比较、稳健性、不确定性和失败运行记录；
- claim map、Methods map、图表契约与引用双检；
- SCI 稿件、修改记录和未解决证据缺口；
- 期刊证据卡、独立模拟评审和投稿前 preflight。

最终状态只会是：

- `NOT_READY_FOR_CONVERSION`
- `BLOCKED`
- `AUTHOR_ACTION_REQUIRED`
- `READY_FOR_HUMAN_SUBMISSION_CHECK`

最后一项表示“可以进入作者/导师的最终人工投稿复核”，不代表同行评审通过，更不代表录用。

---

## 架构速览

```text
SKILL.md                         轻量入口与路由
references/forge-trace-*.md     五阶段与质量轨
references/model-validation-*  八类模型验证菜单
scripts/forge.py                工作区、阶段门与变更传播
scripts/run_pipeline.py         S1–S7 兼容运行时
scripts/readiness/              投稿就绪兼容检查
config/forge-trace.yaml         框架与硬规则
tests/                           确定性回归测试
assets/brand/                    品牌主视觉
```

来源、许可与有意舍弃的设计见 [`references/provenance.md`](references/provenance.md)。

---

## 验证

```bash
python -m pytest -q
python scripts/check_docs.py
python scripts/forge.py --help
```

测试通过只说明确定性代码和工件契约符合预期。真实论文仍需要作者、领域专家和目标期刊的人工判断。

## License

本仓库原创代码与文本采用 MIT License。第三方模板、语料和资产保留各自许可；不要把未授权论文全文或付费模板打包进本 skill。
