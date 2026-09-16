# Research Mother｜通用科研母 Skill + 可替换领域包

**从文献到证据，从代码到方法，从结果到论文。** 首个领域包：空间天气与中间层—低热层（MLT）温度响应。

## 这是什么
一个可上传的 Agent Skill、按阶段调用的科研模块集合，以及可执行的辅助脚本。不是训练新模型，不是保证自动产出可发表结果，也不是所有上游平台的通用安装器。

原创研究和综述走不同路线；目标期刊的风格根据真实全文语料提炼，而不是套一个“顶刊万能模板”。上游五个项目保留独立版本和许可，母 Skill 不运行它们的全局安装脚本。

## 现在有什么
- 统一总控、领域提炼、检索/综述、框架、数据分析/方法描述、绘图、补稿、期刊风格、润色及审查模块。
- Crossref 分页检索、DOI 规范化、去重、在线/纸本/收录日期区分、原始响应与失败日志。`published` 用于时间窗口发现，`indexed` 用于补捞延迟收录或更新的记录。检索结果必须再做相关性和全文筛选。
- PDF 授权下载与逐页文本提取；页码、哈希、重复文件、解析失败和阅读状态都有记录。
- 期刊卡片编译：单刊单体裁、作者组隔离、留出评测、来源位置、支持篇数/分母；不能把重复作者当独立证据。
- 补稿结构校验、正文重复长片段提示、输入变化后的下游失效检测、可重复打包。

`modules/` 中的分析、写作和语义审查由承载 Skill 的模型执行；不是 Python 已经自动完成的研究。`scripts/` 明确列出的确定性工具才是本地可执行功能。

## 最简单的 GPT 用法
有 Skills 入口时：Plugins → Skills → Create → Upload from your computer，上传单独的 `research-mother` 安装 ZIP，不要上传整个旧建模仓库。以账号界面实际扫描和安装结果为准。官方说明： https://help.openai.com/en/articles/20001066-skills-in-chatgpt 。可用范围和入口可能随账号/工作区不同。

没有该入口时，把 ZIP 上传到普通对话并要求解压、完整读取 SKILL.md 和相关模块；这是当次会话使用，不等于永久安装。可访问 GitHub 的会话也可读取本目录入口，然后按需加载模块。仓库更新不会自动同步已上传的副本。

安装后可说：
> 使用 research-mother，加载 space-weather-mlt 领域包。基于我上传的资料启动研究，先建立证据矩阵，再按原创研究路线推进。补稿只增加有实质贡献的比较、方法依据或机制约束，不堆防御性文字。没有证据的结果不要写。

学习期刊可说：
> 使用 research-mother 学习这批目标期刊 PDF。先核验期刊、体裁、版本和作者组，逐篇读全文及相关图表，保留一部分作者组做留出评测。提炼篇章组织与论证动作，不复制原句；规则没有通过留出评测前标为草案。

## 本地运行（Windows / macOS / Linux）
进入本目录；建议 Python 3.10 以上。
```bash
python -m pip install -r requirements.txt
python scripts/research.py doctor
python -m unittest discover -s tests -v
python scripts/research.py init runs/my-study
python scripts/research.py search --query "geomagnetic storm mesosphere lower thermosphere temperature SABER" --since 2026-08-17 --until 2026-09-16 --out runs/search-20260916
python scripts/research.py search --query "geomagnetic storm SABER" --since 2026-08-17 --until 2026-09-16 --mode indexed --out runs/indexed-20260916
```
日期只是命令示例，实际使用时修改；定期发现必须同时考虑延迟收录。无需模型 API Key 的是这些确定性工具，不代表所有上游工具都免费或不需要密钥。

下载/编目操作与 JSON 示例见 `docs/CONTRACTS.md`。每次使用新输出目录，保留之前结果；失败不会被报告为“没有新文献”。默认未开启任何后台订阅或 GitHub 定时任务。

## 上游集成与许可
见 `docs/UPSTREAM.md`。`config/upstream.lock.json` 锁定五个真实提交。运行：
```bash
python scripts/upstream.py --out vendor-cache
```
这会将五个上游源码 ZIP 拉取到隔离缓存并记录状态，**不会自动在 GPT 安装**。未通过当前环境的工具/依赖/许可检查前，不启用上游脚本或 hooks。Source staged ≠ installed ≠ invocation tested。

## 隐私与版本
原始论文、未发表稿件、私有数据、API Key 不提交到公开 GitHub。工作目录和上游缓存默认忽略；发行 ZIP 只收录明确允许的源码目录。实际打包前仍须人工/模型复核待发布文件。

当前版是可测试的 v0.1.0 原型。没有真实期刊语料就没有真实期刊学习成果；没有项目数据就没有实际科研分析结果。改良效果需通过留出论文、实际任务和研究者盲评验证，不能由程序测试数替代。
