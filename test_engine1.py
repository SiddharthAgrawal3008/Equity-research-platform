"""
Engine 1 — Quick validation test.
Run from the project root: python test_engine1.py [TICKER]
Default ticker is AAPL.
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

from backend.engines.financial_data import fetch_raw
from backend.engines.engine1_standardizer import standardize

TICKER = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

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

print("\n=== NEW FIELDS (last 3 years) ===")
print(f"  Cost of Revenue:     {[round(x,1) if x is not None else None for x in f.cost_of_revenue[-3:]]}")
print(f"  D&A:                 {[round(x,1) if x is not None else None for x in f.depreciation_amortisation[-3:]]}")
print(f"  Pre-tax Income:      {[round(x,1) if x is not None else None for x in f.pre_tax_income[-3:]]}")
print(f"  Tax Expense:         {[round(x,1) if x is not None else None for x in f.tax_expense[-3:]]}")
print(f"  R&D:                 {[round(x,1) if x is not None else None for x in f.research_and_development[-3:]]}")
print(f"  SG&A:                {[round(x,1) if x is not None else None for x in f.selling_general_admin[-3:]]}")
print(f"  Long-term Debt:      {[round(x,1) if x is not None else None for x in f.long_term_debt[-3:]]}")
print(f"  Total Equity:        {[round(x,1) if x is not None else None for x in f.total_equity[-3:]]}")
print(f"  Accounts Payable:    {[round(x,1) if x is not None else None for x in f.accounts_payable[-3:]]}")
print(f"  Net Debt:            {[round(x,1) if x is not None else None for x in f.net_debt[-3:]]}")
print(f"  Net Working Capital: {[round(x,1) if x is not None else None for x in f.net_working_capital[-3:]]}")
print(f"  Free Cash Flow:      {[round(x,1) if x is not None else None for x in f.free_cash_flow[-3:]]}")
print(f"  Net Debt Issuance:   {[round(x,1) if x is not None else None for x in f.net_debt_issuance[-3:]]}")

print("\n=== DIVIDENDS PAID (last 3) ===")
print(f.dividends_paid[-3:])
print("\n=== SHARE BUYBACKS (last 3) ===")
print(f.share_buybacks[-3:])
print("\n=== QUALITY WARNINGS ===")
for w in out.quality["warnings"]:
    print(" -", w)
print("\n=== META ===")
print(f"Ticker: {out.meta.ticker}")
print(f"Price:  {out.meta.current_price}")
print(f"EV:     {out.meta.enterprise_value:.1f}M")
print(f"Years of history: {out.quality['years_of_history']}")

from backend.engines.engine1_derived import compute_derived
out = compute_derived(out)

print("\n=== MARGINS (latest year) ===")
for k, v in out.margins.items():
    print(f"  {k}: {v[-1]:.4f}" if v[-1] is not None else f"  {k}: None")

print("\n=== GROWTH ===")
print(f"  revenue_cagr: {out.growth['revenue_cagr']:.4f}" if out.growth['revenue_cagr'] is not None else "  revenue_cagr: None")
print(f"  revenue_yoy last 3: {out.growth['revenue_yoy'][-3:]}")
print(f"  fcf_yoy last 3: {out.growth['fcf_yoy'][-3:]}")

print("\n=== RETURNS (latest year) ===")
print(f"  roe:  {out.returns['roe'][-1]:.4f}" if out.returns['roe'][-1] is not None else "  roe: None")
print(f"  roa:  {out.returns['roa'][-1]:.4f}" if out.returns['roa'][-1] is not None else "  roa: None")
print(f"  roic: {out.returns['roic'][-1]:.4f}" if out.returns['roic'][-1] is not None else "  roic: None")

print("\n=== EFFICIENCY (latest year) ===")
for k, v in out.efficiency.items():
    print(f"  {k}: {v[-1]:.2f}" if v[-1] is not None else f"  {k}: None")

print("\n=== TREND FLAGS ===")
for k, v in out.trend_flags.items():
    print(f"  {k}: {v}")

from backend.engines.engine1_ttm import compute_ttm
out = compute_ttm(out, raw)
print("\n=== TTM ===")
for k, v in out.ttm.items():
    print(f"  {k}: {v}")

from backend.engines.engine1_market_data import build_market_data
market_data, md_warnings = build_market_data(out.meta.ticker, out.meta.current_price)
out.market_data = market_data
out.quality["warnings"].extend(md_warnings)
print("\n=== MARKET DATA ===")
print(f"  daily_close  : {len(out.market_data['daily_close'])} pts  first={out.market_data['daily_close'][:1]}  last={out.market_data['daily_close'][-1:]}")
print(f"  daily_dates  : {out.market_data['daily_dates'][:1]} … {out.market_data['daily_dates'][-1:]}")
print(f"  weekly_close : {len(out.market_data['weekly_close'])} pts  first={out.market_data['weekly_close'][:1]}  last={out.market_data['weekly_close'][-1:]}")
print(f"  weekly_dates : {out.market_data['weekly_dates'][:1]} … {out.market_data['weekly_dates'][-1:]}")
print(f"  bench daily  : {len(out.market_data['benchmark_daily_close'])} pts")
print(f"  bench weekly : {len(out.market_data['benchmark_weekly_close'])} pts")
print(f"  current_price: {out.market_data['current_price']}")
print(f"  benchmark    : {out.market_data['benchmark_ticker']}")
if md_warnings:
    print("\n=== MARKET DATA WARNINGS ===")
    for w in md_warnings:
        print(f"  - {w}")

from backend.engines.engine1_validator import validate
validate(out)
print("\n=== VALIDATION RESULTS ===")
print(f"  is_valid:                  {out.quality['is_valid']}")
print(f"  balance_sheet_balanced:    {out.quality.get('balance_sheet_balanced')}")
print(f"  is_negative_equity:        {out.quality.get('is_negative_equity')}")
print(f"  net_income_cf_reconciled:  {out.quality.get('net_income_cf_reconciled')}")
print(f"  errors ({len(out.quality['errors'])}):")
for e in out.quality["errors"]:
    print(f"    [ERROR] {e}")
print(f"  warnings ({len(out.quality['warnings'])}):")
for w in out.quality["warnings"]:
    print(f"    [WARN]  {w}")
