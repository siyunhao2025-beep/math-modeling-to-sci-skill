from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "prompts" / "09-language-polish.md"
QUALITY_PROMPT = ROOT / "prompts" / "03-quality-assessment.md"


def test_defensive_revision_has_auditable_dispositions():
    text = PROMPT.read_text(encoding="utf-8")
    for disposition in ("KEEP", "TIGHTEN", "REFRAME", "RELOCATE", "CUT", "QUERY"):
        assert f"`{disposition}`" in text
    assert "location | function | disposition" in text


def test_revision_preserves_load_bearing_scientific_content():
    text = PROMPT.read_text(encoding="utf-8")
    for protected in ("主张上限", "来源状态", "竞争解释", "负结果", "非显著结果"):
        assert protected in text
    assert "不得重选指标来隐藏不利结果" in text
    assert "不能用“删得更多”" in text


def test_quality_assessment_does_not_enforce_a_universal_sentence_quota():
    text = QUALITY_PROMPT.read_text(encoding="utf-8")
    assert "平均 18–25 词" not in text
    assert "无超 40 词" not in text
    assert "主语、比较项、条件和指代" in text
    assert "目标期刊" in text


def test_reader_clarity_contract_keeps_reasoning_and_scientific_register():
    text = PROMPT.read_text(encoding="utf-8")
    for requirement in (
        "完整句子",
        "主体—动作—对象",
        "比较对象",
        "适用条件",
        "必要的中间步骤",
        "逐词直译",
        "自造缩写",
        "信息充分之后再精简",
    ):
        assert requirement in text
    assert "目标期刊或学科语体" in text
    assert "通俗化不得替换已锁定的专业术语" in text
