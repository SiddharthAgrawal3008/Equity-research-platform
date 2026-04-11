"""
Engine 1 — Quick validation test.
Run from the project root: python test_engine1.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from backend.engines.financial_data import fetch_raw
from backend.engines.engine1_standardizer import standardize

TICKER = "AAPL"

print(f"Fetching {TICKER} from Alpha Vantage + Finnhub...")
raw = fetch_raw(TICKER)
print(f"Raw pull done: {len(raw['annual_income'])} annual periods received")

out = standardize(raw)
m = out.meta
f = out.financials
q = out.quality

print()
print("=== COMPANY META ===")
print(f"  Ticker:           {m.ticker}")
print(f"  Name:             {m.company_name}")
print(f"  Sector:           {m.sector}")
print(f"  Industry:         {m.industry}")
print(f"  Exchange:         {m.exchange}")
print(f"  Currency:         {m.currency}")
print(f"  Price:            ${m.current_price:.2f}")
print(f"  Market Cap:       ${m.market_cap:,.1f}M")
print(f"  Enterprise Value: ${m.enterprise_value:,.1f}M")
print(f"  Shares Out:       {m.shares_outstanding:.1f}M")

print()
print("=== ANNUAL FINANCIALS (USD millions, oldest -> newest) ===")
print(f"  Years:            {f.years}")
print(f"  Revenue:          {[round(x, 1) if x is not None else None for x in f.revenue]}")
print(f"  Gross Profit:     {[round(x, 1) if x is not None else None for x in f.gross_profit]}")
print(f"  EBIT:             {[round(x, 1) if x is not None else None for x in f.ebit]}")
print(f"  EBITDA:           {[round(x, 1) if x is not None else None for x in f.ebitda]}")
print(f"  Net Income:       {[round(x, 1) if x is not None else None for x in f.net_income]}")
print(f"  Interest Exp:     {[round(x, 1) if x is not None else None for x in f.interest_expense]}")
print(f"  Total Assets:     {[round(x, 1) if x is not None else None for x in f.total_assets]}")
print(f"  Total Debt:       {[round(x, 1) if x is not None else None for x in f.total_debt]}")
print(f"  Cash:             {[round(x, 1) if x is not None else None for x in f.cash_and_equivalents]}")
print(f"  Retained Earn:    {[round(x, 1) if x is not None else None for x in f.retained_earnings]}")
print(f"  Op. Cash Flow:    {[round(x, 1) if x is not None else None for x in f.operating_cash_flow]}")
print(f"  Capex:            {[round(x, 1) if x is not None else None for x in f.capex]}")

print()
print("=== DATA QUALITY FLAGS ===")
print(f"  is_valid:         {q['is_valid']}")
print(f"  years_of_history: {q['years_of_history']}")
print(f"  is_bank:          {q['is_bank']}")
print(f"  is_reit:          {q['is_reit']}")
print(f"  warnings:         {q['warnings']}")
print(f"  errors:           {q['errors']}")
