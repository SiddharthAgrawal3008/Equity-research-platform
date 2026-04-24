"""
test_e5.py — Smoke test for Engine 5 against the full pipeline.

Run from the project root:
    python backend/engines/engine_5/test_e5.py

Prints PASS / FAIL for each assertion and exits non-zero on any failure.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.pipeline.orchestrator import run_pipeline
from backend.engines import DEFAULT_ENGINES
from backend.engines.engine_5.data_extractor import extract

EXPECTED_SECTIONS = {
    "business_summary",
    "financial_performance",
    "valuation_range",
    "key_risks",
    "investment_thesis",
    "bear_case",
}

failures: list[str] = []

def check(label: str, condition: bool, detail: str = "") -> None:
    marker = "PASS" if condition else "FAIL"
    msg = f"  [{marker}] {label}"
    if not condition and detail:
        msg += f"\n         → {detail}"
    print(msg)
    if not condition:
        failures.append(label)


print("Running Engine 5 smoke test (ticker: AAPL)...")
print()

result = run_pipeline("AAPL", DEFAULT_ENGINES)
r      = result.get("report", {})
d      = extract(result, r.get("available_sections", []))

# ── Report-level assertions ───────────────────────────────────────────────────

check(
    "report status is 'success'",
    r.get("status") == "success",
    f"got: {r.get('status')!r}",
)

sections = r.get("sections", {})
missing  = EXPECTED_SECTIONS - set(sections.keys())
check(
    "all 6 section keys present",
    not missing,
    f"missing: {missing}",
)

check(
    "no section is empty",
    all(isinstance(v, str) and len(v) > 10 for v in sections.values()),
    "one or more sections returned an empty or trivially short string",
)

pdf = r.get("pdf_base64")
check(
    "pdf_base64 is non-empty",
    isinstance(pdf, str) and len(pdf) > 100,
    f"pdf_base64 length: {len(pdf) if isinstance(pdf, str) else pdf!r}",
)

# ── Data extraction assertions ────────────────────────────────────────────────

check(
    "beta is not None",
    d.beta is not None,
    "beta extraction failed — check E3 market_risk shape",
)

check(
    "beta_benchmark is 'S&P 500'",
    d.beta_benchmark == "S&P 500",
    f"got: {d.beta_benchmark!r}",
)

check(
    "Altman Z is not None",
    d.altman_z is not None,
    "financial_health extraction failed",
)

check(
    "TTM revenue is not None",
    d.ttm_revenue is not None,
    "ttm revenue extraction failed — check E1 output",
)

check(
    "no PDF generation warnings",
    not any("PDF" in w for w in r.get("warnings", [])),
    str([w for w in r.get("warnings", []) if "PDF" in w]),
)

# ── Summary ───────────────────────────────────────────────────────────────────

print()
if failures:
    print(f"RESULT: FAIL — {len(failures)} assertion(s) failed: {failures}")
    sys.exit(1)
else:
    print(f"RESULT: PASS — all {9} assertions passed.")
    sys.exit(0)
