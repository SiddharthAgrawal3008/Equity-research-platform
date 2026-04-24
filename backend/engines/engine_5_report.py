"""
Engine 5 — Auto-Generated Investment Memo (Owner: Naman)
=========================================================

Input:  financial_data, valuation, risk_metrics, nlp_insights (from bus)
Output: report (to bus)

Responsibilities:
    - Consume all bus data from upstream engines
    - Generate a structured IB-style research note:
        1. Business summary
        2. Financial performance overview
        3. Valuation range
        4. Key risks
        5. Investment thesis
        6. Bear case
    - Gracefully handle missing sections if upstream engines failed

TODO (Naman): Replace the stub below with real implementation.
"""

from backend.pipeline.base_engine import BaseEngine


class ReportEngine(BaseEngine):
    name = "engine_5"
    requires = ["financial_data", "valuation", "risk_metrics", "nlp_insights"]
    produces = "report"

    def run(self, context: dict) -> dict:
        # Check which upstream engines succeeded — adapt report accordingly
        status = context["status"]
        available_sections = []

        if status.get("engine_1") == "success":
            available_sections.append("financial_data")
        if status.get("engine_2") == "success":
            available_sections.append("valuation")
        if status.get("engine_3") == "success":
            available_sections.append("risk_metrics")
        if status.get("engine_4") == "success":
            available_sections.append("nlp_insights")

        # ----- STUB: replace with real report generation -----
        # Real implementation should:
        # 1. Check available_sections to decide which report parts to generate
        # 2. If valuation is missing: omit valuation section, add warning note
        # 3. If risk_metrics is missing: omit risk section, add warning note
        # 4. If nlp_insights is missing: omit NLP section (minimal impact)
        # 5. Format everything into a structured investment memo
        # 6. Return dict matching the report bus key schema
        warnings = []
        if "valuation" not in available_sections:
            warnings.append("Valuation engine unavailable — valuation section omitted.")
        if "risk_metrics" not in available_sections:
            warnings.append("Risk engine unavailable — risk section omitted.")
        if "nlp_insights" not in available_sections:
            warnings.append("NLP engine unavailable — sentiment section omitted.")

        return {
            "summary": "STUB — real investment memo not yet generated.",
            "sections": {},
            "available_sections": available_sections,
            "warnings": warnings,
        }
