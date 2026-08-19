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

    ethics_applies = study["human_participants"] or study["animal_study"]
    check("E01", "ethics/IRB/animal approval statement", has(text, r"ethics|IRB|institutional review board|approved by|animal care|IACUC"), "blocker", ethics_applies, "Never fabricate approval IDs.")
    check("E02", "informed consent statement", has(text, r"informed consent|consent was obtained|waiver of consent"), "blocker", study["human_participants"])
    check("E03", "data availability statement", has(text, r"data availability|data are available|data available|repository|zenodo|figshare|dryad|osf"), "blocker", True)
    check("E04", "conflict of interest / competing interests", has(text, r"conflict of interest|competing interests?|declare no conflict"), "blocker", True)
    check("E05", "funding statement", has(text, r"funding|funded by|grant|financial support|no specific funding"), "warning", True)

    blockers = [c for c in checks if c["status"] == "MISSING" and c["severity"] == "blocker"]
    warnings = [c for c in checks if c["status"] == "MISSING" and c["severity"] == "warning"]
    result = {
        "schema_version": "1.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "study_signals": study,
        "recommended_reporting_guidelines": guidelines,
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
