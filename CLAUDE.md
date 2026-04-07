# Equity Research Platform — Project Memory

## CRITICAL: Engine Ownership (DO NOT MIX)

| Engine | Owner | Responsibility |
|--------|-------|----------------|
| **Engine 1** | **Divyansh** | Financial Data Engine |
| **Engine 2** | **Siddharth** | Main Valuation Engine ("The Heart") |
| **Engine 3** | **Siddharth** | Risk & Financial Health Engine |
| **Engine 4** | **Annant** | NLP Intelligence Engine |
| **Engine 5** | **Naman** | Auto-Generated Investment Memo |

**Rule:** Each person only modifies their own engine(s). Never mix responsibilities across owners.

## CRITICAL: Branch Strategy

| Member | Branch | Can Touch |
|--------|--------|-----------|
| **Divyansh** | `dev/divyansh` | Engine 1 + Frontend only |
| **Siddharth** | `dev/siddharth` | Engine 2 + Engine 3 only |
| **Annant** | `dev/annant` | Engine 4 only |
| **Naman** | `dev/naman` | Engine 5 only |

- `main` is protected — never push directly
- Before working, the user MUST tell you which engine they're working on
- Based on that, checkout their branch and only modify their files
- All 4 members share this Claude account — always confirm identity/engine before coding

---

## Engine Specs

### Engine 1 — Financial Data Engine (Divyansh)
- **Input:** Company ticker
- **Process:**
  - Pull income statement, balance sheet, cash flow
  - Standardize line items
  - Handle missing values
  - Compute trailing twelve months (TTM)
- **Output:** Structured financial dataset (Contract A)

---

### Engine 2 — Main Valuation Engine (Siddharth) ⭐ Main Engine
- **1. Discounted Cash Flow (DCF) Model**
  - Forecast revenue growth
  - Operating margin projection
  - Capex assumptions
  - Working capital changes
  - WACC calculation
  - Terminal value
- **2. Relative Valuation**
  - EV/EBITDA
  - P/E
  - P/B
  - Compare to industry peers
- **3. Sensitivity Analysis**
  - Growth vs WACC heatmap
  - Terminal growth sensitivity
- **4. Monte Carlo Simulation**
  - Randomized growth assumptions
  - Valuation distribution output

---

### Engine 3 — Risk & Financial Health Engine (Siddharth)
- Beta calculation
- Historical volatility
- Sharpe ratio
- Max drawdown
- Value at Risk (VaR)
- Altman Z-score
- Interest coverage ratio
- Debt to EBITDA

---

### Engine 4 — NLP Intelligence Engine (Annant)
- **Input:** Annual report PDFs, earnings call transcripts
- **Process:**
  - Sentiment analysis
  - Risk word frequency
  - Tone shift year over year
  - Topic modeling
- **Output:**
  - Risk summary
  - Management optimism score
  - Red flag indicators

---

### Engine 5 — Auto-Generated Investment Memo (Naman)
Generates a formatted IB-style research note with:
1. Business summary
2. Financial performance overview
3. Valuation range
4. Key risks
5. Investment thesis
6. Bear case
