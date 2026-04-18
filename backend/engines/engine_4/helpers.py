"""
Engine 4 — Schema Helpers & Contract Validator
===============================================
Provides valid_fallback_schema (safe default output) and
validate_contract (used by tests and smoke runs).
"""

from __future__ import annotations

import datetime

MODEL_VERSION = "1.0.0"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def valid_fallback_schema(warnings: list[str] | None = None) -> dict:
    """Return the full 34-field nlp_insights contract with safe defaults.

    Called whenever E4 cannot complete its work — guarantees E5 always
    receives a schema-valid dict. All list fields are [] (never None);
    scalar fields use None where data is unavailable.
    """
    warn_list: list[str] = list(warnings) if warnings else []
    if not warn_list:
        warn_list = ["Engine 4 failed — NLP section unavailable"]

    return {
        "sentiment": {
            "status": "failed",
            "overall_score": None,
            "management_optimism": None,
            "risk_word_frequency": None,
            "uncertainty_score": None,
            "forward_guidance_tone": None,
            "sentiment_trend": None,
            "qna_vs_prepared_delta": None,
        },
        "red_flags": {
            "status": "failed",
            "flags": [],
            "flags_count": 0,
            "severity": None,
            "categories_detected": [],
            "new_vs_prior": None,
        },
        "key_themes": {
            "status": "failed",
            "themes": [],
            "theme_scores": None,
            "emerging_themes": [],
            "fading_themes": [],
            "financial_alignment": None,
        },
        "source_coverage": {
            "status": "failed",
            "earnings_transcripts": 0,
            "annual_reports": 0,
            "total_documents": 0,
            "date_range_start": None,
            "date_range_end": None,
            "most_recent_quarter": None,
            "staleness_flag": True,
            "sources_list": [],
        },
        "meta": {
            "computed_at": _now_iso(),
            "model_version": MODEL_VERSION,
            "nlp_approach": "none",
            "warnings": warn_list,
            "data_quality_flag": "minimal",
            "assumptions": {},
        },
    }


# ── Contract shape ────────────────────────────────────────────────────

_REQUIRED_SHAPE: dict[str, list[str]] = {
    "sentiment": [
        "status", "overall_score", "management_optimism",
        "risk_word_frequency", "uncertainty_score",
        "forward_guidance_tone", "sentiment_trend",
        "qna_vs_prepared_delta",
    ],
    "red_flags": [
        "status", "flags", "flags_count", "severity",
        "categories_detected", "new_vs_prior",
    ],
    "key_themes": [
        "status", "themes", "theme_scores",
        "emerging_themes", "fading_themes", "financial_alignment",
    ],
    "source_coverage": [
        "status", "earnings_transcripts", "annual_reports",
        "total_documents", "date_range_start", "date_range_end",
        "most_recent_quarter", "staleness_flag", "sources_list",
    ],
    "meta": [
        "computed_at", "model_version", "nlp_approach",
        "warnings", "data_quality_flag", "assumptions",
    ],
}

_LIST_FIELDS: set[tuple[str, str]] = {
    ("red_flags", "flags"),
    ("red_flags", "categories_detected"),
    ("key_themes", "themes"),
    ("key_themes", "emerging_themes"),
    ("key_themes", "fading_themes"),
    ("source_coverage", "sources_list"),
    ("meta", "warnings"),
}


def validate_contract(output: dict) -> tuple[bool, list[str]]:
    """Verify that an nlp_insights dict matches the 34-field contract.

    Returns (is_valid, errors). errors is empty when is_valid is True.
    """
    errors: list[str] = []

    for section, fields in _REQUIRED_SHAPE.items():
        if section not in output:
            errors.append(f"Missing section: {section}")
            continue
        sub = output[section]
        if not isinstance(sub, dict):
            errors.append(f"{section} is not a dict")
            continue
        for field in fields:
            if field not in sub:
                errors.append(f"Missing field: {section}.{field}")

    for section, field in _LIST_FIELDS:
        val = output.get(section, {}).get(field)
        if val is None:
            errors.append(f"{section}.{field} must be [] not None")

    return (len(errors) == 0, errors)
