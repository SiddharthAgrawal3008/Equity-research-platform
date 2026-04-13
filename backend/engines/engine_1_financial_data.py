"""
Engine 1 — Financial Data Engine (Owner: Divyansh)
===================================================

Input:  ticker (from bus)
Output: financial_data (to bus)

Responsibilities:
    - Pull income statement, balance sheet, cash flow (FMP API, yfinance)
    - Standardize line items
    - Handle missing values
    - Compute trailing twelve months (TTM)

TODO (Divyansh): Replace the stub below with real implementation.
"""

from backend.pipeline.base_engine import BaseEngine
from backend.engines.mock_bus_data import MOCK_FINANCIAL_DATA


class FinancialDataEngine(BaseEngine):
    name = "engine_1"
    requires = ["ticker"]
    produces = "financial_data"

    def run(self, context: dict) -> dict:
        ticker = context["ticker"]

        # ----- STUB: replace with real data fetching -----
        # Real implementation should:
        # 1. Fetch financial statements via FMP API / yfinance using `ticker`
        # 2. Standardize line items across data sources
        # 3. Handle missing values (interpolation / fill)
        # 4. Compute TTM figures
        # 5. Return dict matching the financial_data bus key schema
        return MOCK_FINANCIAL_DATA
