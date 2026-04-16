"""
Engine 4 — NLP Intelligence Engine (Owner: Annant)
===================================================

Input:  financial_data (from bus) + external transcripts
Output: nlp_insights (to bus)

Responsibilities:
    - Sentiment analysis on annual reports and earnings calls
    - Risk word frequency analysis
    - Tone shift detection (year over year)
    - Topic modeling
    - Management optimism scoring
    - Red flag identification

TODO (Annant): Replace the stub below with real implementation.
"""

from backend.pipeline.base_engine import BaseEngine
from backend.engines.mock_bus_data import MOCK_NLP_INSIGHTS


class NLPEngine(BaseEngine):
    name = "engine_4"
    requires = ["financial_data"]
    produces = "nlp_insights"

    def run(self, context: dict) -> dict:
        financial_data = context["financial_data"]

        # ----- STUB: replace with real NLP analysis -----
        # Real implementation should:
        # 1. Fetch earnings call transcripts and annual report PDFs
        # 2. Run sentiment analysis
        # 3. Compute risk word frequency
        # 4. Detect tone shifts year over year
        # 5. Perform topic modeling
        # 6. Score management optimism
        # 7. Identify red flags
        # 8. Return dict matching the nlp_insights bus key schema
        return MOCK_NLP_INSIGHTS
