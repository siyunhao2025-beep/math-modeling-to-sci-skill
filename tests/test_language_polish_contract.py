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
