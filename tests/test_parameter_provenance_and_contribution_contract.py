from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_parameter_identity_and_model_internal_claims_are_explicit():
    matrix = _text("references/model-validation-matrix.md")
    for token in (
        "identified_parameter",
        "calibrated_parameter",
        "model_internal",
        "has_sampling_distribution",
        "support_or_extrapolation_boundary",
    ):
        assert token in matrix

    assert "不能把校准参数写成已由样本识别" in matrix
    assert "不能把模型内输出写成观测证据" in matrix
    assert "没有抽样分布" in matrix


def test_error_correction_cannot_be_market_as_contribution():
    playbook = _text("references/conversion-playbook.md")
    prompt = _text("prompts/02-academic-rewrite.md")

    for text in (playbook, prompt):
        assert "correction_not_contribution" in text
        assert "有效基线" in text
        assert "重跑受影响结果" in text
        assert "披露" in text


def test_2026_10_06_sources_and_boundaries_are_recorded():
    provenance = _text("references/provenance.md")
    for token in (
        "bobbyZhong10/empirical-workflow-kit",
        "36171fc659613d590ac9b44f9059d4070ac1d2d3",
        "ysyecust/write-reader-first-papers",
        "110dd76a6cb7f76dd29ed3954dcdff2de5c2f48b",
        "Avi7ii/journal-figure-polish",
        "cbb3cf7f7ec416e2b8f0bf82a1d77bd703c32dd7",
    ):
        assert token in provenance

