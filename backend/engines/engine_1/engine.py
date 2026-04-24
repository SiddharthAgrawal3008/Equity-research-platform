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
"""

from dataclasses import asdict

from backend.pipeline.base_engine import BaseEngine
from backend.engines.engine_1.financial_data import fetch_raw
from backend.engines.engine_1.standardizer import standardize
from backend.engines.engine_1.derived import compute_derived
from backend.engines.engine_1.ttm import compute_ttm
from backend.engines.engine_1.market_data import build_market_data
from backend.engines.engine_1.validator import validate


class FinancialDataEngine(BaseEngine):
    name = "engine_1"
    requires = ["ticker"]
    produces = "financial_data"

    def run(self, context: dict) -> dict:
        ticker = context["ticker"]

        raw = fetch_raw(ticker)
        output = standardize(raw)
        output = compute_derived(output)
        output = compute_ttm(output, raw)

        market_data, md_warnings = build_market_data(
            output.meta.ticker, output.meta.current_price
        )
        output.market_data = market_data
        output.quality["warnings"].extend(md_warnings)

        validate(output)

        return self._to_bus_dict(output)

    @staticmethod
    def _to_bus_dict(output) -> dict:
        financials = asdict(output.financials)
        years = financials.pop("years")  # lift to top level

        meta = asdict(output.meta)
        meta["sector"] = (meta.get("sector") or "Unknown").upper()  # match E3 sector keys

        return {
            "meta":           meta,
            "quality":        output.quality,
            "years":          years,
            "financials":     financials,
            "ttm":            output.ttm,
            "market_data":    output.market_data,
            "margins":        output.margins,
            "growth":         output.growth,
            "returns":        output.returns,
            "efficiency":     output.efficiency,
            "cost_structure": output.cost_structure,
            "trend_flags":    output.trend_flags,
        }
