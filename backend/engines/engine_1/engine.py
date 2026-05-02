"""
Engine 1 — Financial Data Engine (Owner: Divyansh)
===================================================

Wires the Step 1–6 sub-modules into the orchestrator's BaseEngine contract:

    fetch_raw          (financial_data.py — parent package)
        ↓
    standardize        (engine1_standardizer.py)
        ↓
    compute_derived    (engine1_derived.py)
        ↓
    compute_ttm        (engine1_ttm.py)
        ↓
    build_market_data  (engine1_market_data.py)
        ↓
    validate           (engine1_validator.py)
        ↓
    _to_bus_dict       (this file)

Reads:  context["ticker"]
Writes: context["financial_data"]
"""

from __future__ import annotations

import logging
from dataclasses import asdict

from backend.engines.engine_1.engine1_derived import compute_derived
from backend.engines.engine_1.engine1_market_data import build_market_data
from backend.engines.engine_1.engine1_standardizer import standardize
from backend.engines.engine_1.engine1_ttm import compute_ttm
from backend.engines.engine_1.engine1_validator import validate
from backend.engines.financial_data import fetch_raw
from backend.engines.shared_context import Engine1Output
from backend.pipeline.base_engine import BaseEngine

logger = logging.getLogger(__name__)


class FinancialDataEngine(BaseEngine):
    name = "engine_1"
    requires = ["ticker"]
    produces = "financial_data"

    def run(self, context: dict) -> dict:
        ticker = context["ticker"]
        try:
            raw = fetch_raw(ticker)
            output = standardize(raw)
            output = compute_derived(output)
            output = compute_ttm(output, raw)

            market_data, md_warnings = build_market_data(
                output.meta.ticker,
                output.meta.current_price,
            )
            output.market_data = market_data
            output.quality.setdefault("warnings", []).extend(md_warnings)

            validate(output)
            return self._to_bus_dict(output)

        except Exception as error:
            logger.exception("Engine 1 failed for ticker %s", ticker)
            return {
                "meta": {"ticker": ticker},
                "quality": {
                    "is_valid": False,
                    "errors": [str(error)],
                    "warnings": [],
                },
            }

    @staticmethod
    def _to_bus_dict(output: Engine1Output) -> dict:
        meta = asdict(output.meta)
        if meta.get("sector"):
            meta["sector"] = meta["sector"].upper()

        financials = asdict(output.financials)
        years = financials.pop("years")

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
