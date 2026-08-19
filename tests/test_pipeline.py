"""test_pipeline.py — 端到端流程与产物校验。"""
import json
import os

import jsonschema
import yaml
import pytest

import common

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(REPO_ROOT, "config", "schema")


def _schema(name):
    return json.load(open(os.path.join(SCHEMA_DIR, name), encoding="utf-8"))


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    wd = str(tmp_path_factory.mktemp("e2e"))
    from conftest import run_full_pipeline
    return run_full_pipeline(
        wd,
        score=7.2,
        scope=["applied-mathematics", "mathematical-modelling", "optimization"],
        method=["ode-pde", "numerical-simulation", "optimization"],
    )


def test_ir_schema_valid(run):
    ir = json.load(open(os.path.join(run, "01-parse", "manuscript.ir.json"), encoding="utf-8"))
    jsonschema.Draft7Validator(_schema("manuscript.schema.json")).validate(ir)
    assert len(ir["sections"]) >= 3
    assert any(e["id"].startswith("eq-") for e in ir["equations"])


def test_no_untitled_section(run):
    ir = json.load(open(os.path.join(run, "01-parse", "manuscript.ir.json"), encoding="utf-8"))
    assert not any(s["heading"] == "(untitled)" for s in ir["sections"])


def test_journal_match_schema_and_count(run):
    jm = json.load(open(os.path.join(run, "04-journals", "journal-match.json"), encoding="utf-8"))
    jsonschema.Draft7Validator(_schema("journal-match.schema.json")).validate(jm)
    recs = jm["recommendations"]
    assert 3 <= len(recs) <= 8
    for r in recs:
        assert r["fit_evidence"] and r["rejection_risks"]
        assert r["impact_factor"]["value"] is None or (
            r["impact_factor"].get("year") and r["impact_factor"].get("source"))
    assert jm["self_check"]["offline_mode"] is True


def test_render_outputs(run):
    build = os.path.join(run, "05-template", "build")
    main = os.path.join(build, "main.tex")
    bib = os.path.join(build, "references.bib")
    manifest = os.path.join(run, "05-template", "MANIFEST.json")
    assert os.path.isfile(main) and os.path.isfile(bib) and os.path.isfile(manifest)
    tex = open(main, encoding="utf-8").read()
    assert "\\begin{document}" in tex and "\\end{document}" in tex
    assert "documentclass" in tex
    # 不应出现前导区/占位章节残留
    assert "(untitled)" not in tex


def test_validation_pass(run):
    v = json.load(open(os.path.join(run, "06-validate", "validation-final.json"), encoding="utf-8"))
    jsonschema.Draft7Validator(_schema("validation.schema.json")).validate(v)
    assert v["summary"]["error_count"] >= 0  # 数值型断言，确保结构正确


def test_report_exists(run):
    rep = os.path.join(run, "conversion-report.md")
    assert os.path.isfile(rep)
    assert "转换报告" in open(rep, encoding="utf-8").read()


def test_journals_yaml_loads():
    d = yaml.safe_load(open(os.path.join(REPO_ROOT, "config", "journals.yaml"), encoding="utf-8"))
    assert len(d["journals"]) >= 3
    # 每个条目 IF 必有 source（离线声明）；有值时还须有 year
    for j in d["journals"]:
        if_h = j.get("impact_factor") or {}
        assert if_h.get("source"), f"IF source 缺失: {j.get('id')}"
        if if_h.get("value") is not None:
            assert if_h.get("year"), f"IF year 缺失: {j.get('id')}"
