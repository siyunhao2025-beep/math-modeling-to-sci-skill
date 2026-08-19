# SCI 写作规范参考（sci-writing-conventions）

> 供 S2 学术化改写与 S6 语言校验参考。机器可校验的规则在 `config/style-rules.yaml`，
> 本文档补充其背景与判据，便于改写时把握"为什么"。

## 1. 时态（Tense）

| 内容 | 时态 | 例 |
|------|------|----|
| 普遍事实 / 公式 / 定义 | 一般现在时 | "The system satisfies ..." |
| 本文所做动作（方法/实验） | 一般过去时或现在时 | "We proposed / propose ..."（现在时更常见） |
| 他人工作 | 现在完成时或过去时 | "Smith et al. (2020) showed ..." |
| 结论与意义 | 一般现在时 | "These results indicate ..." |

常见错误：在方法章节用将来时；在陈述普遍规律时用过去时。

## 2. 语态（Voice）

- 方法/实验描述可用被动（"The data were collected ..."）或主动（"We collected ..."）。
- 现代趋势偏向主动、以作者为主语（"We derive ..."），更清晰、责任明确。
- 避免在摘要/结论大量堆砌 "It is believed that ..."、"It can be seen that ..." 之类弱主语句式。

## 3. 禁用 / 慎用表达

见 `style-rules.yaml#banned_words` 与 `hedging` 配置。要点：

- **绝对化**：avoid "clearly", "obviously", "it is evident that"——除非真有不容置疑的证据。
- **空泛强调**：avoid "very", "extremely", "quite"——用具体量值替代。
- **模糊量化**：avoid "some", "many", "several" 无数字支撑；改为具体百分比/数量。
- **营销腔**：avoid "novel", "first time ever", "groundbreaking" 除非可证。

## 4.  hedging（审慎表述）

学术主张应可证伪、留有余地：

- 强："Our method solves the problem." → 弱化为 "Our method mitigates the problem under the assumed conditions."
- 用 "suggests", "indicates", "is consistent with" 替代 "proves"（除非严格证明）。

## 5. 数字与单位（Numbers & Units）

- 依据 `style-rules.yaml#numbers_units`：小于 10 的整数拼写（"three"）或按期刊要求用数字；
  含小数点/单位时一律用数字（"3.5 km"）。
- SI 单位，量与单位间留空格（"5 kg" 非 "5kg"）。
- 范围用 en dash 或 "to"（"10–20" 或 "10 to 20"），避免连字符。

## 6. 符号与术语一致性

- 同一符号全文含义唯一（由 IR `symbol_map` 保证）；重命名须记录 `renamed_from`。
- 缩写首次出现写全称（"Ordinary Differential Equation (ODE)"），之后可用缩写。

## 7. CJK 残留

- 目标语言为 en 时，正文/图表 caption/参考文献外文标题不得残留中日韩字符。
- 中文输入法误入的标点（全角，、。；）亦属禁止，应使用半角。

## 8. 引用

- 引用须可验证（DOI/来源）。不可凭记忆写参考文献。
- 引用样式（numbered / author-year）必须与目标期刊 `constraints.reference_style` 一致。
- 正文 `\cite` 与 `references.bib` 必须双向一致（G6-03）。
