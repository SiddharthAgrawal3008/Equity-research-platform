"""Backend engines for the Equity Research Platform."""

from backend.engines.engine_1_financial_data import FinancialDataEngine
from backend.engines.engine_2.valuation import ValuationEngine
from backend.engines.engine_3_risk import RiskEngine
from backend.engines.engine_4_nlp import NLPIntelligenceEngine
from backend.engines.engine_5_report import ReportEngine

DEFAULT_ENGINES = [
    FinancialDataEngine(),
    ValuationEngine(),
    RiskEngine(),
    NLPIntelligenceEngine(),
    ReportEngine(),
]

__all__ = [
    "FinancialDataEngine",
    "ValuationEngine",
    "RiskEngine",
    "NLPIntelligenceEngine",
    "ReportEngine",
    "DEFAULT_ENGINES",
]
