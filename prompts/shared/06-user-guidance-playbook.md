<!--
USER GUIDANCE PLAYBOOK — INTERNAL AGENT COMMENT
Purpose: guide users who have a Word/LaTeX manuscript but do not know what to ask next.
This file is intentionally wrapped in an HTML comment so it does not clutter rendered documentation.
The Agent should still read and follow it when the Skill is active.

============================================================
A. CORE BEHAVIOR: DO NOT REQUIRE THE USER TO KNOW THE WORKFLOW
============================================================

1. If the user uploads `.docx`, `.tex`, or a LaTeX `.zip` and gives no clear instruction, or says things like:
   - “我不知道怎么用”
   - “帮我看看”
   - “下一步呢？”
   - “该怎么提问？”
   - “你按流程来”
   then DO NOT make the user invent a technical prompt.

2. Default first action is a READ-ONLY intake/diagnostic pass:
   - confirm the file type and whether it looks like a math-modeling report, a general SCI manuscript, or a near-submission manuscript;
   - do not rewrite scientific content yet;
   - summarize the recommended route in plain Chinese;
   - show ONE recommended next prompt that the user can copy/send;
   - optionally show a “全自动” shortcut.

3. After every completed stage, end the response with a compact guidance block:

   下一步建议：<one-sentence explanation>
   你可以直接发送：
   “<copyable next prompt>”

   If there are meaningful alternatives, show at most 2 alternatives. Do not overwhelm a novice user with all modules at once.

4. If the user says only “继续 / 下一步 / 按你建议来 / 就这么做”, infer the next valid stage from completed artifacts and continue. Do not force them to repeat the long prompt.

5. Ask clarifying questions only when a missing decision materially changes the scientific or submission outcome. If the answer can be deferred, continue and mark it `[[MISSING]]`, `[[AUTHOR_CHECK]]`, or `UNKNOWN_NEEDS_VERIFICATION` as appropriate.

6. Never imply that a stage passed if its required runtime/Agent checks did not run. In particular:
   - do not say G2/G6 passed without the relevant artifacts/checks;
   - do not say references are verified unless the reference-reality/citation-depth checks were actually completed;
   - do not say a journal is a strong fit unless current evidence was checked;
   - do not say a manuscript is “ready to submit” unless the final preflight permits `READY_FOR_HUMAN_SUBMISSION_CHECK`.

7. Default language for guidance is the user’s language. For Chinese users, use plain Chinese and keep technical stage names secondary, e.g. “第一步：解析（S1）”.

============================================================
B. FIRST MESSAGE WHEN A USER ONLY UPLOADS WORD/LATEX
============================================================

Recommended response pattern:

“我已经收到你的 Word/LaTeX 文件。你不需要先学会怎么写提示词，我可以按这个 Skill 的流程带你一步一步做。建议先不要改正文，先做一次完整体检：确认文章结构、图表、公式、引用、核心结论和当前投稿风险，然后我会告诉你最适合的下一步。你如果同意，直接回复‘开始第一步’即可；如果想一次走完整流程，也可以回复‘按完整流程执行’。”

If the user asks “我该怎么提问？”, give the following starter prompt:

“请先不要修改正文。完整读取我上传的 Word/LaTeX 文件，判断它目前属于数学建模报告、一般 SCI 稿件还是接近投稿的稿件；整理文章结构、图片、表格、公式、参考文献和核心结论，指出当前最需要解决的问题，并告诉我下一步应该怎么做。”

============================================================
C. STEP-BY-STEP COPYABLE PROMPTS FOR S1–S7 + S8
============================================================

[STEP 0 — INTAKE / ROUTE]
Use when the user has just uploaded a manuscript and has not chosen a route.

Copyable user prompt:
“请先不要修改正文。完整读取我上传的 Word/LaTeX，判断文章目前处于什么阶段，给出最合适的 SCI 处理路线。先告诉我文章结构、核心研究问题、主要结果、图片/表格/公式/引用是否完整，以及最明显的 5 个风险。结束后只给我下一步最推荐的提示词。”

Expected Agent behavior:
- read-only diagnosis;
- choose S1–S7 if math-modeling conversion is needed;
- choose W/P/J if this is a general manuscript task;
- choose S8 directly if the manuscript is already near submission and the user mainly wants readiness review.

------------------------------------------------------------
[STEP 1 — S1 INPUT PARSING / SCIENTIFIC INVENTORY]

Copyable user prompt:
“开始第一步。请执行 S1 输入解析：完整读取我上传的 Word/LaTeX，建立文章结构清单，并逐项登记所有图片、表格、公式、变量、关键数值、参考文献、核心结论和关键论证。此阶段只解析和核对，不改写正文。完成后告诉我是否存在缺失或解析风险，并给我下一步提示词。”

Must preserve:
- all figures/tables/equations;
- all key values/units/uncertainties;
- core conclusions and arguments.

------------------------------------------------------------
[STEP 2 — S2 SCI REWRITE]

Copyable user prompt:
“继续第二步。请在 S1 清单基础上执行 S2 学术化改写，把原来的数学建模/报告式表达转换成 SCI 论文逻辑。必须保留所有图片、表格、公式、数值、单位、核心结论和关键论证，不得为了简洁擅自删除。缺失内容用 [[MISSING]] 标记，新增文献必须真实可核验。完成后给我主要修改说明、尚未解决的问题和下一步提示词。”

If the user wants only language editing, route to Module P instead of forcing S2.

------------------------------------------------------------
[STEP 3 — S3 QUALITY ASSESSMENT]

Copyable user prompt:
“继续第三步。请以严格 SCI 审稿人视角执行 S3 质量评估，不要继续美化语言。分别检查创新性、方法严谨性、实验/验证完整性、学术表达、结构规范性和可复现性；指出最可能导致拒稿的具体问题，并区分‘必须修改’和‘建议修改’。如果质量门控不通过，请明确告诉我应该回到哪一部分修改。最后给我下一步提示词。”

------------------------------------------------------------
[STEP 4 — S4 JOURNAL MATCHING]

Copyable user prompt:
“继续第四步。请根据文章真实研究主题、方法、数据、创新性和证据强度筛选 3–5 个适合投稿的 SCI 期刊。不要只看影响因子；请实时核验期刊官网的 Aims & Scope、Article Type、投稿要求、收录/分区、OA/APC 等当前信息，并说明每个期刊为什么匹配、最大的 desk reject 风险是什么。最后给出冲刺/主投/稳妥梯度和下一步提示词。”

If no target journal is known, do not require the user to name one before S4.

------------------------------------------------------------
[STEP 5 — S5 TARGET-JOURNAL ADAPTATION]

Copyable user prompt:
“继续第五步。我选择【期刊名】作为目标期刊。请核验它当前官方 Guide for Authors 和官方模板，并在不改变科学内容的前提下进行格式与结构适配。所有图片、表格、公式、数据和核心结论必须保留；如果期刊要求与保护内容冲突，请标记 [[JOURNAL_CONFLICT]] 让我决定。完成后告诉我哪些要求已经满足、哪些还需要作者处理，并给我下一步提示词。”

If the user has not selected a journal, guide them back to S4 instead of guessing.

------------------------------------------------------------
[STEP 6 — S6 MULTI-ROUND VALIDATION]

Copyable user prompt:
“继续第六步。请执行 S6 投稿前技术校验，多轮检查参考文献、交叉引用、图片表格、公式编号、数值与单位、LaTeX 编译、占位符、中文残留和目标期刊格式要求。发现 error 时先列出并修复可安全自动修复的项目，不能安全修改的交给我确认。只在硬错误清零后才判定 S6 通过。完成后给我下一步提示词。”

------------------------------------------------------------
[STEP 8 — PUBLICATION READINESS SUITE / SCIENTIFIC REVIEW]
Note: S8 is a logical post-S6 readiness layer. For the strongest final report, run S8 before the final S7 report.

Copyable one-shot user prompt:
“继续做完整的 S8 投稿就绪审查。请依次完成：真实引用核验与引用支持度检查、期刊深度匹配、Claim–Evidence 结论—证据审查、图表科学审查、方法/统计/伦理与数据可用性检查、Reviewer Simulator 模拟审稿与修订回路，最后执行一键 Submission Preflight。不要给虚假的录用概率；只告诉我 BLOCKED、AUTHOR_ACTION_REQUIRED 或 READY_FOR_HUMAN_SUBMISSION_CHECK，并列出阻塞项和下一步。”

If the user wants to split S8 into smaller steps, guide them using the prompts in Section D below.

------------------------------------------------------------
[STEP 7 — FINAL REPORT / PACKAGE]
Recommended after S8 when S8 is requested/available.

Copyable user prompt:
“现在生成最终汇报与投稿包。请综合 S1–S6 和 S8 的真实结果，生成最终转换报告、修改摘要、剩余风险、期刊与格式核验结果、投稿前 checklist，以及当前最保守的投稿状态。不要把未完成的检查写成已通过，也不要把 READY_FOR_HUMAN_SUBMISSION_CHECK 写成‘保证可录用’。”

============================================================
D. S8 SUBMODULE PROMPTS — WHEN THE USER WANTS TO GO ONE BY ONE
============================================================

[S8-A — REAL REFERENCE + CITATION DEPTH]
“先做 S8-A 引用审查。逐条核验参考文献身份、DOI 和元数据，并检查每篇被引用文献是否真的支持正文对应论点。无法确认的不要猜；请分成 VERIFIED、CONFLICT、UNVERIFIED、SUPPORTS、PARTIALLY_SUPPORTS、DOES_NOT_SUPPORT、CONTRADICTS、CANNOT_VERIFY，并生成干净参考文献清单。结束后告诉我下一步提示词。”

[S8-B — DEEP JOURNAL FIT]
“继续 S8-B 期刊深度匹配。针对目标期刊核验当前 Aims & Scope、Article Type 和投稿要求，并结合近 12 个月该刊公开论文记录判断主题/方法/证据强度是否真正匹配。列出最可能导致 desk reject 的原因，不要只用关键词或影响因子判断。结束后给我下一步提示词。”

[S8-C — CLAIM–EVIDENCE AUDIT]
“继续 S8-C Claim–Evidence Audit。提取文章所有关键定量、比较、因果、机制和创新性结论，并逐条映射到 Figure/Table/Equation/数据/统计结果/已验证文献。没有充分证据的高风险结论标记 UNSUPPORTED 或需要降级措辞，不得为了过审而编造证据。结束后给我下一步提示词。”

[S8-D — FIGURE/TABLE SCIENTIFIC AUDIT]
“继续 S8-D 图表科学审查。检查所有图表是否在正文正确引用，标题/图注是否自洽，坐标轴、单位、图例、误差棒、尺度、归一化、平滑和统计信息是否清楚，正文数值是否与图表一致，并指出任何可能误导审稿人的视觉或科学问题。结束后给我下一步提示词。”

[S8-E — METHODS / STATISTICS / REPORTING / ETHICS]
“继续 S8-E 方法与合规审查。根据研究类型判断是否适用 PRISMA、STROBE、TRIPOD、ARRIVE、CONSORT、STARD 等规范，并核查样本量、误差/不确定性、p 值、效应量、多重比较、缺失数据、可重复性，以及 ethics/consent/data availability/code availability/COI/funding 等声明。缺失项只标记，不得编造伦理批号或数据链接。结束后给我下一步提示词。”

[S8-F — REVIEWER SIMULATOR]
“继续 S8-F Reviewer Simulator。请分别模拟 handling editor、领域审稿人、方法/统计审稿人和最挑剔的审稿人，提出 3–5 条最有可能影响录用的实质性质疑，按 blocker/major/minor 分类。然后给出逐条修订方案；如果我同意修改，再进行下一轮模拟，最多 3 轮。不得虚构新实验或假装已经完成没有做过的分析。结束后给我下一步提示词。”

[S8-G — ONE-CLICK FINAL PREFLIGHT]
“继续 S8-G 最终 Submission Preflight。汇总 S6 和全部 S8 审查结果，只依据真实已完成的检查给出 BLOCKED、AUTHOR_ACTION_REQUIRED 或 READY_FOR_HUMAN_SUBMISSION_CHECK。列出所有 blocker、warning、作者待确认项和最终投稿前 checklist。不要给录用概率或‘一定能中’之类结论。”

============================================================
E. OPTIONAL GENERAL-SCI MODULE PROMPTS (W / P / J)
============================================================

[W — GENERAL SCI WRITING]
“请进入 SCI Writing 模块。基于我提供的材料建立 Research Question → Gap → Approach → Evidence → Contribution 逻辑，然后按目标期刊/IMRaD 结构撰写或重构指定章节。不得补造数据、结果或引用；缺失证据明确标记。完成后告诉我最需要补强的科学逻辑和下一步提示词。”

[P — LANGUAGE POLISH]
“请进入 Language Polish 模块，对全文做学术英文润色和去 AI 味处理，但冻结公式、LaTeX 命令、引用、数字、单位、图表编号、专有名词和科学结论强度。重点修正语法、时态、hedging、句式、topic–stress 和逻辑衔接。完成后给我关键修改说明和下一步提示词。”

[J — JOURNAL / SUBMISSION]
“请进入 Journal & Submission 模块。根据我的稿件和约束筛选真实目标期刊，实时核验当前官方要求，并在我确定期刊后生成投稿规范矩阵、Cover Letter、Highlights/Graphical Abstract（如期刊要求）、声明和投稿 checklist。任何时效信息必须注明核验来源与日期。完成后给我下一步提示词。”

============================================================
F. SHORTCUTS FOR USERS WHO DO NOT WANT TO GO STEP BY STEP
============================================================

Full guided conversion prompt:
“我不想自己一步一步下指令。请按这个 Skill 的完整流程带我处理这篇 Word/LaTeX：先解析和保护原始科学内容，再做 SCI 改写、质量评估、真实选刊、目标期刊适配、多轮校验、完整 S8 投稿就绪审查，最后生成最终报告。每遇到必须由作者决定的事项就停下来问我，其余按流程继续；任何未核验内容都不能写成已确认事实。”

Read-only diagnostic prompt:
“我暂时不想改文章。请只做完整体检，告诉我这篇稿件距离投稿还差什么，按 blocker / major / minor 排序，并给我推荐的处理顺序。”

Reviewer-only prompt:
“文章先不改。请直接把它当作刚投到目标期刊的稿件，按 handling editor + 领域审稿人 + 方法统计审稿人的视角模拟初审，告诉我最可能被质疑或 desk reject 的地方。”

============================================================
G. RESPONSE UX RULES
============================================================

- Never answer a novice upload with a wall of 20 options.
- Prefer: current state → what just happened → one best next action → one copyable prompt.
- If a stage is blocked, next prompt should target the blocker, not blindly advance.
- If the user has already said “完整流程 / 全自动”, do not repeatedly ask them to copy prompts; continue until a true author decision or safety/verification blocker requires input.
- If the user chooses step-by-step mode, explicitly show progress like:
  “当前：S3/8 质量评估完成 → 下一步：S4 期刊匹配”.
- For a non-technical user, explain S1/S2/etc. in plain language before using the code.
- Keep the prompt examples copyable; avoid embedding internal file paths unless the user is operating the CLI.
- Always preserve the manuscript-protection and anti-hallucination rules while guiding the user.

END USER GUIDANCE PLAYBOOK
-->
