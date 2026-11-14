#!/usr/bin/env python3
"""Heuristic reporting-guideline, methods/statistics and ethics compliance audit.

The detector recommends relevant guideline families and flags missing high-level
reporting elements. It does not copy or replace the official checklists; the
Agent must verify the current official checklist at execution time.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from readiness.utils import ir_text, load_json, save_json  # noqa: E402


def text_from(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".json":
        try:
            return ir_text(load_json(path))
        except Exception:
            pass
    return p.read_text(encoding="utf-8")


def has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.I | re.S))


DATA_STATEMENT = re.compile(
    r"\bdata(?:\s+and\s+code)?\s+availability\b|"
    r"\bavailability\s+of\s+(?:the\s+)?data\b|"
    r"\bdata(?:\s+and\s+(?:source\s+)?code)?\s+"
    r"(?:are|is|will\s+be)\s+(?:publicly\s+)?(?:available|deposited|archived|included)\b|"
    r"\b(?:supporting|underlying|processed|raw)\s+data\b.{0,120}"
    r"\b(?:available|deposited|archived|included)\b",
    re.I | re.S,
)
CODE_STATEMENT = re.compile(
    r"\bcode\s+availability\b|\bavailability\s+of\s+(?:the\s+)?code\b|"
    r"\b(?:data\s+and\s+)?(?:analysis\s+|source\s+|custom\s+)?code\s+"
    r"(?:are|is|will\s+be)\s+(?:publicly\s+)?(?:available|deposited|archived|included)\b|"
    r"\b(?:analysis|source|custom)\s+code\b.{0,120}"
    r"\b(?:available|deposited|archived|included)\b",
    re.I | re.S,
)
URL = re.compile(r"https?://[^\s<>()\[\]{}]+", re.I)
DOI = re.compile(r"(?:doi\s*:\s*|https?://doi\.org/)10\.\d{4,9}/[^\s<>()\[\]{}]+", re.I)
ACCESSION = re.compile(
    r"\b(?:GSE\d+|GSM\d+|SR[APRX]\d+|ERR\d+|PRJ(?:NA|EB|DB)\d+|"
    r"PDB\s*:?[A-Za-z0-9]{4}|E-MTAB-\d+)\b",
    re.I,
)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def _statement_context(text: str, pattern: re.Pattern[str]) -> str:
    """Return only statement paragraphs, not unrelated links elsewhere in a paper."""
    blocks = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    selected: list[str] = []
    for index, block in enumerate(blocks):
        if not pattern.search(block):
            continue
        selected.append(block)
        heading = re.sub(r"[#*:._-]", " ", block).strip()
        if len(heading) <= 80 and index + 1 < len(blocks):
            selected.append(blocks[index + 1])
    return "\n".join(selected)


def _subject_context(context: str, kind: str) -> str:
    """Keep a combined data/code paragraph from satisfying the other statement."""
    own = DATA_STATEMENT if kind == "data" else CODE_STATEMENT
    other = CODE_STATEMENT if kind == "data" else DATA_STATEMENT
    selected: list[str] = []
    active = False
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", context):
        sentence = sentence.strip()
        if not sentence:
            continue
        own_hit = bool(own.search(sentence))
        other_hit = bool(other.search(sentence))
        if other_hit and not own_hit:
            active = False
            continue
        if own_hit:
            active = True
        if active:
            selected.append(sentence)
    return " ".join(selected)


def availability_statement(text: str, kind: str) -> dict:
    """Classify whether a data/code statement names an actionable access route.

    This is deliberately an offline pre-screen.  A syntactically plausible DOI,
    accession or URL is not treated as resolved or accessible.
    """
    if kind not in {"data", "code"}:
        raise ValueError("kind must be data or code")
    context = _statement_context(text, DATA_STATEMENT if kind == "data" else CODE_STATEMENT)
    if not context:
        return {
            "status": "MISSING",
            "actionable": False,
            "concrete_locator_present": False,
            "persistent_identifier_present": False,
            "restriction_reason_present": False,
            "access_route_present": False,
            "logged_out_access_check": "NOT_APPLICABLE_UNTIL_ROUTE_EXISTS",
        }
    context = _subject_context(context, kind)

    request_only = has(
        context,
        r"available\s+(?:from\s+[^.]{0,80}\s+)?(?:upon|on)\s+(?:reasonable\s+)?request|"
        r"requests?\s+(?:may|can)\s+be\s+made",
    )
    restriction_reason = has(
        context,
        r"(?:because|due\s+to|owing\s+to|cannot\s+be\s+(?:shared|public))[^.]{0,160}"
        r"(?:privacy|confidential|consent|ethic|legal|licen[cs]|commercial|sensitive|restriction)",
    )
    access_route = bool(EMAIL.search(context)) or has(
        context,
        r"data\s+access\s+committee|access\s+application|apply\s+(?:at|through|to)|"
        r"requests?\s+(?:must|should|may|can)\s+be\s+(?:sent|submitted)\s+to",
    )
    persistent_identifier = bool(DOI.search(context) or ACCESSION.search(context))
    concrete_locator = persistent_identifier or bool(URL.search(context))
    subject = "data" if kind == "data" else "(?:analysis|source|custom)?\\s*code"
    in_article = has(
        context,
        subject
        + r".{0,80}(?:included|provided).{0,80}"
        + r"(?:this\s+(?:article|manuscript)|supplement(?:ary|al)|source\s+data)",
    )
    not_applicable = has(
        context,
        subject + r"\s+(?:sharing|availability)\s+is\s+not\s+applicable",
    )
    has_rationale = has(
        context,
        r"(?:because|as\s+this|no\s+(?:new|custom)\s+(?:data|code)|"
        r"theoretical|review\s+article|did\s+not\s+(?:generate|create|analyse|analyze))",
    )

    # A restricted application page is a route, not evidence that the material
    # itself is public.  Classify the restriction before generic URLs.
    if restriction_reason and (access_route or concrete_locator):
        status = "RESTRICTED_WITH_REASON_AND_ROUTE"
        actionable = True
        access_route = True
    elif concrete_locator:
        status = "PUBLIC_WITH_LOCATOR"
        actionable = True
    elif in_article:
        status = "IN_ARTICLE_OR_SUPPLEMENT"
        actionable = True
    elif not_applicable and has_rationale:
        status = "NOT_APPLICABLE_WITH_RATIONALE"
        actionable = True
    elif request_only:
        status = "VAGUE_REQUEST_ONLY"
        actionable = False
    else:
        status = "PRESENT_WITHOUT_ROUTE"
        actionable = False

    return {
        "status": status,
        "actionable": actionable,
        "concrete_locator_present": concrete_locator,
        "persistent_identifier_present": persistent_identifier,
        "restriction_reason_present": restriction_reason,
        "access_route_present": access_route,
        "logged_out_access_check": (
            "REQUIRED_AT_SUBMISSION" if concrete_locator or access_route else "NOT_APPLICABLE_UNTIL_ROUTE_EXISTS"
        ),
    }


def run(manuscript: str, out: str) -> dict:
    text = text_from(manuscript)
    lower = text.lower()
    study = {
        "systematic_review": has(text, r"systematic review|meta-analysis|meta analysis"),
        "observational_study": has(text, r"cohort|case[- ]control|cross[- ]sectional|observational study"),
        "prediction_model": has(text, r"prediction model|prognostic model|diagnostic model|machine learning model"),
        "animal_study": has(text, r"\b(mouse|mice|rat|rats|animal experiment|in vivo)\b"),
        "randomized_trial": has(text, r"randomi[sz]ed (?:controlled )?trial|\bRCT\b"),
        "diagnostic_accuracy": has(text, r"diagnostic accuracy|sensitivity and specificity|ROC curve|AUC"),
        "human_participants": has(text, r"human participants|patients|participants|subjects|institutional review board|IRB"),
    }
    guidelines = []
    mapping = {
        "systematic_review": "PRISMA",
        "observational_study": "STROBE",
        "prediction_model": "TRIPOD",
        "animal_study": "ARRIVE",
        "randomized_trial": "CONSORT",
        "diagnostic_accuracy": "STARD",
    }
    for k, name in mapping.items():
        if study[k]:
            guidelines.append({"name": name, "reason": k, "official_checklist_status": "VERIFY_AT_RUNTIME"})

    checks = []
    def check(cid, label, ok, severity="warning", applies=True, note=None):
        checks.append({"id": cid, "label": label, "applies": applies, "status": "PASS" if ok else ("MISSING" if applies else "NOT_APPLICABLE"), "severity": severity if applies and not ok else "info", "note": note})

    stats_present = has(text, r"\bp\s*[<=>]\s*0?\.\d+|confidence interval|\bCI\b|standard deviation|standard error|error bar")
    check("M01", "sample-size rationale / power statement", has(text, r"sample size|power analysis|power calculation"), "warning", stats_present or study["human_participants"] or study["animal_study"])
    check("M02", "error bars or uncertainty are defined", has(text, r"error bars?.*(?:represent|show|denote)|mean\s*[±\\pm]|standard deviation|standard error|confidence interval"), "blocker", stats_present)
    check("M03", "exact p-value/reporting convention", has(text, r"\bp\s*[<=>]\s*0?\.\d+|p-values? were|statistical significance"), "warning", has(text, r"statistical|significant|hypothesis test|t-test|anova|regression"))
    check("M04", "effect size / uncertainty interval", has(text, r"effect size|confidence interval|credible interval|odds ratio|hazard ratio|relative risk|Cohen"), "warning", study["human_participants"] or stats_present)
    check("M05", "multiple-testing handling", has(text, r"multiple compar|Bonferroni|false discovery|FDR|Benjamini"), "warning", has(text, r"multiple comparisons?|multiple testing|many hypotheses"))
    check("M06", "missing-data handling", has(text, r"missing data|missing values|imputation|complete-case"), "warning", study["human_participants"])
    check("M07", "randomization/blinding statement", has(text, r"randomi[sz]|blind(?:ed|ing)|mask(?:ed|ing)"), "warning", study["randomized_trial"] or study["animal_study"])
    check("R01", "reproducibility/software/version statement", has(text, r"software|version|code|repository|github|zenodo|figshare|osf|seed"), "warning", True)

    data_availability = availability_statement(text, "data")
    code_availability = availability_statement(text, "code")
    code_applies = has(
        text,
        r"\b(custom|analysis|source)\s+code\b|\bpython\b|\bmatlab\b|"
        r"\br\s+(?:package|script)\b|\bsimulation\b|\bsoftware\s+(?:implementation|package)\b",
    )
    check(
        "R02",
        "actionable code availability statement",
        code_availability["actionable"],
        "warning",
        code_applies,
        "A repository name without a locator is not an access route; verify public links while logged out.",
    )
    check(
        "R03",
        "versioned or persistent public code locator",
        code_availability["persistent_identifier_present"]
        or has(_statement_context(text, CODE_STATEMENT), r"\b(?:release|tag|commit)\b"),
        "warning",
        code_applies and code_availability["status"] == "PUBLIC_WITH_LOCATOR",
        "A mutable repository landing page does not identify the exact code used for the paper.",
    )

    ethics_applies = study["human_participants"] or study["animal_study"]
    check("E01", "ethics/IRB/animal approval statement", has(text, r"ethics|IRB|institutional review board|approved by|animal care|IACUC"), "blocker", ethics_applies, "Never fabricate approval IDs.")
    check("E02", "informed consent statement", has(text, r"informed consent|consent was obtained|waiver of consent"), "blocker", study["human_participants"])
    check(
        "E03",
        "actionable data availability statement",
        data_availability["actionable"],
        "blocker",
        True,
        "Public data need a concrete locator; restricted data need both a reason and a request route. Verify locators while logged out.",
    )
    check(
        "E06",
        "persistent public data identifier",
        data_availability["persistent_identifier_present"],
        "warning",
        data_availability["status"] == "PUBLIC_WITH_LOCATOR",
        "A URL is concrete but may be mutable; prefer a DOI or repository accession when available.",
    )
    check("E04", "conflict of interest / competing interests", has(text, r"conflict of interest|competing interests?|declare no conflict"), "blocker", True)
    check("E05", "funding statement", has(text, r"funding|funded by|grant|financial support|no specific funding"), "warning", True)

    blockers = [c for c in checks if c["status"] == "MISSING" and c["severity"] == "blocker"]
    warnings = [c for c in checks if c["status"] == "MISSING" and c["severity"] == "warning"]
    result = {
        "schema_version": "1.1",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "study_signals": study,
        "recommended_reporting_guidelines": guidelines,
        "availability_statement_audit": {
            "data": data_availability,
            "code": code_availability,
            "important_limit": (
                "Locator syntax is checked offline. Existence, permissions, license terms, "
                "and reproducibility require submission-time human verification; a PASS here "
                "does not prove that artifacts are accessible or independently reproducible."
            ),
        },
        "checks": checks,
        "summary": {"blockers": len(blockers), "warnings": len(warnings), "guidelines_to_verify": len(guidelines)},
        "blockers": [c["id"] for c in blockers],
        "warnings": [c["id"] for c in warnings],
        "important_limit": "Guideline selection and checklist completion require Agent/human verification against the current official guideline; this file is a pre-screen, not certification.",
    }
    save_json(out, result)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = run(args.manuscript, args.out)
    print(f"blockers={result['summary']['blockers']} warnings={result['summary']['warnings']} -> {args.out}")
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
