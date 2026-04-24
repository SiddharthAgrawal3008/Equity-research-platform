import yfinance as yf
aapl = yf.Ticker("AAPL")
print("=== CASH FLOW STATEMENT (annual) ===")
cf = aapl.cashflow
print(cf.to_string())
print("\n=== INCOME STATEMENT (annual) ===")
inc = aapl.income_stmt
print(inc.to_string())
print("\n=== BALANCE SHEET (annual) ===")
bs = aapl.balance_sheet
print(bs.to_string())
