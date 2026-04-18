"""
Context Factory — Creates the shared data bus for each pipeline run.
====================================================================

The context dict is the single communication channel between all engines.
Each pipeline run gets a fresh context via create_context(ticker).
"""


def create_context(ticker: str) -> dict:
    """Create a fresh data bus dictionary for one pipeline run.

    Args:
        ticker: The stock ticker to analyze (e.g., "AAPL").

    Returns:
        A context dict with all bus keys initialized to empty dicts,
        status tracking per engine, error log, and pipeline metadata.
    """
    return {
        "ticker": ticker,
        "financial_data": {},
        "valuation": {},
        "risk_metrics": {},
        "nlp_insights": {},
        "report": {},
        "status": {
            "engine_1": "pending",
            "engine_2": "pending",
            "engine_3": "pending",
            "engine_4": "pending",
            "engine_5": "pending",
        },
        "errors": [],
        "metadata": {
            "started_at": None,
            "completed_at": None,
            "stages_completed": [],
        },
    }
