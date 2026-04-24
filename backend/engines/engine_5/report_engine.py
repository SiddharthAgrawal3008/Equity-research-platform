"""
report_engine.py — Engine 5 orchestrator (Owner: Naman).

Reads the four upstream bus keys, builds ReportData, generates all
six narrative sections, renders a PDF, and returns the report bus key.
"""

from __future__ import annotations
import logging

from backend.pipeline.base_engine import BaseEngine
from backend.engines.engine_5.data_extractor import extract
from backend.engines.engine_5 import narrative as narr
from backend.engines.engine_5.pdf_builder import build_pdf_base64

logger = logging.getLogger(__name__)


class ReportEngine(BaseEngine):
    name     = "engine_5"
    requires = ["financial_data", "valuation", "risk_metrics", "nlp_insights"]
    produces = "report"

    def run(self, context: dict) -> dict:
        status = context.get("status", {})

        available_sections: list[str] = []
        if status.get("engine_1") == "success":
            available_sections.append("financial_data")
        if status.get("engine_2") == "success":
            available_sections.append("valuation")
        if status.get("engine_3") == "success":
            available_sections.append("risk_metrics")
        if status.get("engine_4") == "success":
            available_sections.append("nlp_insights")

        warnings: list[str] = []
        if "valuation"    not in available_sections:
            warnings.append("Valuation engine unavailable — valuation section omitted.")
        if "risk_metrics" not in available_sections:
            warnings.append("Risk engine unavailable — risk section omitted.")
        if "nlp_insights" not in available_sections:
            warnings.append("NLP engine unavailable — sentiment section omitted.")

        d = extract(context, available_sections)

        sections: dict[str, str] = {}

        if "financial_data" in available_sections:
            sections["business_summary"]      = narr.business_summary(d)
            sections["financial_performance"] = narr.financial_performance(d)
        else:
            warnings.append("Financial data unavailable — business summary omitted.")

        if "valuation" in available_sections:
            sections["valuation_range"] = narr.valuation_range(d)

        risk_text = narr.key_risks(d)
        if risk_text and risk_text != "Key risk data unavailable.":
            sections["key_risks"] = risk_text

        sections["investment_thesis"] = narr.investment_thesis(d)
        sections["bear_case"]         = narr.bear_case(d)

        summary = narr.summary_line(d)

        # PDF generation — never fails the engine; degrades to None on error
        pdf_base64: str | None = None
        try:
            pdf_base64 = build_pdf_base64(d, sections, warnings)
        except Exception as exc:
            logger.exception("PDF generation failed")
            warnings.append(f"PDF generation failed: {exc}")

        return {
            "status":             "success",
            "summary":            summary,
            "sections":           sections,
            "available_sections": available_sections,
            "warnings":           warnings,
            "pdf_base64":         pdf_base64,
        }
