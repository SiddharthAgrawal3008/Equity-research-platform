"""
Engine 3 — Red Flag Detector
==============================

Scans financial statement data for warning signs — patterns that signal
trouble in a company's financials.  Runs 6 rule-based checks against
data from the shared context bus and returns a list of human-readable
flag strings that Engine 5 can drop directly into a report's risk section.

This module does NOT call any external API and does NOT import from
other Engine 3 modules.  The pre-computed Altman Z-score is passed in
as a parameter to avoid duplicate work.
"""

from __future__ import annotations

import logging

from backend.engines.shared_config import EARNINGS_QUALITY_HIGH_THRESHOLD, ZSCORE_DISTRESS

logger = logging.getLogger(__name__)


def _growth(old, new):
    """Compute growth rate. Returns None if old is 0 or None."""
    if old is None or new is None or old == 0:
        return None
    return (new - old) / old


def detect_red_flags(
    financial_data: dict,
    altman_z_score: float | None = None,
) -> list[str]:
    """Scan financial statement data for warning signs.

    Args:
        financial_data: The full financial_data dict from the context bus.
        altman_z_score: Pre-computed Z-score from the financial_health module.
                        Passed in to avoid recomputing. None if not applicable.

    Returns:
        List of triggered flag strings. Empty list if no flags triggered.
        Each string is human-readable with evidence baked in.
    """
    financials = financial_data.get("financials", {})
    years = financial_data.get("years", [])
    flags: list[str] = []

    # ── Flag 1: Weak Earnings Quality ─────────────────────────────────
    try:
        ocf = financials.get("operating_cash_flow", [])
        ni = financials.get("net_income", [])
        window = min(5, len(ocf), len(ni))
        if window > 0:
            count = 0
            checked = 0
            for i in range(len(ocf) - window, len(ocf)):
                if ocf[i] is not None and ni[i] is not None:
                    checked += 1
                    if ocf[i] < ni[i]:
                        count += 1
            if checked > 0 and count >= 3:
                flags.append(
                    f"Operating cash flow below net income in {count} of "
                    f"{checked} years — weak earnings quality"
                )
                logger.debug("Flag 1 triggered: earnings quality (%d/%d)", count, checked)
            else:
                logger.debug("Flag 1 not triggered: earnings quality (%d/%d)", count, checked)
    except Exception as exc:
        logger.warning("Flag 1 (earnings quality) check failed: %s", exc)

    # ── Flag 2: Receivables Growing Faster Than Revenue ───────────────
    try:
        rev = financials.get("revenue", [])
        ar = financials.get("accounts_receivable", [])
        if len(rev) >= 3 and len(ar) >= 3 and len(years) >= 3:
            rev_old, rev_new = rev[-3], rev[-1]
            ar_old, ar_new = ar[-3], ar[-1]
            if all(v is not None for v in (rev_old, rev_new, ar_old, ar_new)):
                rev_g = _growth(rev_old, rev_new)
                ar_g = _growth(ar_old, ar_new)
                if rev_g is not None and ar_g is not None and rev_g > 0:
                    if ar_g > 2 * rev_g:
                        ratio = ar_g / rev_g
                        start_year = years[-3]
                        end_year = years[-1]
                        flags.append(
                            f"Receivables growing {ratio:.1f}x faster than "
                            f"revenue ({start_year}-{end_year}) — possible "
                            f"channel stuffing"
                        )
                        logger.debug("Flag 2 triggered: AR/Rev ratio=%.1f", ratio)
                    else:
                        logger.debug("Flag 2 not triggered: AR growth within bounds")
                else:
                    logger.debug("Flag 2 skipped: revenue growth zero or negative")
            else:
                logger.debug("Flag 2 skipped: None values in AR or revenue")
        else:
            logger.debug("Flag 2 skipped: fewer than 3 years of data")
    except Exception as exc:
        logger.warning("Flag 2 (receivables vs revenue) check failed: %s", exc)

    # ── Flag 3: Rapid Leverage Increase ───────────────────────────────
    try:
        debt = financials.get("total_debt", [])
        ebitda = financials.get("ebitda", [])
        worst_increase = 0.0
        worst_prev = 0.0
        worst_curr = 0.0
        worst_year = None
        n = min(len(debt), len(ebitda), len(years))
        for i in range(1, n):
            if (debt[i - 1] is not None and debt[i] is not None
                    and ebitda[i - 1] is not None and ebitda[i] is not None
                    and ebitda[i - 1] > 0 and ebitda[i] > 0):
                prev_ratio = debt[i - 1] / ebitda[i - 1]
                curr_ratio = debt[i] / ebitda[i]
                increase = curr_ratio - prev_ratio
                if increase > worst_increase:
                    worst_increase = increase
                    worst_prev = prev_ratio
                    worst_curr = curr_ratio
                    worst_year = years[i]
        if worst_increase > 1.0:
            flags.append(
                f"Debt/EBITDA increased from {worst_prev:.1f}x to "
                f"{worst_curr:.1f}x in {worst_year} — rapid leverage increase"
            )
            logger.debug("Flag 3 triggered: leverage spike in %s", worst_year)
        else:
            logger.debug("Flag 3 not triggered: max D/EBITDA increase=%.2f", worst_increase)
    except Exception as exc:
        logger.warning("Flag 3 (leverage increase) check failed: %s", exc)

    # ── Flag 4: Altman Z-Score in Distress Zone ──────────────────────
    try:
        if altman_z_score is not None and altman_z_score < ZSCORE_DISTRESS:
            flags.append(f"Altman Z-score {altman_z_score:.2f} — in distress zone")
            logger.debug("Flag 4 triggered: Z=%.2f < %.2f", altman_z_score, ZSCORE_DISTRESS)
        else:
            logger.debug(
                "Flag 4 not triggered: Z=%s (threshold=%.2f)",
                altman_z_score, ZSCORE_DISTRESS,
            )
    except Exception as exc:
        logger.warning("Flag 4 (Altman distress) check failed: %s", exc)

    # ── Flag 5: Goodwill Concentration Risk ───────────────────────────
    try:
        gw = financials.get("goodwill", [])
        ta = financials.get("total_assets", [])
        if gw and ta and len(gw) > 0 and len(ta) > 0:
            gw_latest = gw[-1]
            ta_latest = ta[-1]
            if gw_latest is not None and ta_latest and ta_latest > 0:
                ratio = gw_latest / ta_latest
                if ratio > 0.30:
                    flags.append(
                        f"Goodwill at {ratio * 100:.0f}% of total assets — "
                        f"significant write-down risk"
                    )
                    logger.debug("Flag 5 triggered: goodwill=%.0f%%", ratio * 100)
                else:
                    logger.debug("Flag 5 not triggered: goodwill=%.0f%%", ratio * 100)
            else:
                logger.debug("Flag 5 skipped: goodwill is None for latest year")
        else:
            logger.debug("Flag 5 skipped: no goodwill data")
    except Exception as exc:
        logger.warning("Flag 5 (goodwill concentration) check failed: %s", exc)

    # ── Flag 6: Negative Free Cash Flow Trend ─────────────────────────
    try:
        fcf = financials.get("free_cash_flow", [])
        window = min(3, len(fcf))
        if window > 0:
            last_n = fcf[-window:]
            valid = [v for v in last_n if v is not None]
            neg_count = sum(1 for v in valid if v < 0)
            if len(valid) > 0 and neg_count >= 2:
                flags.append(
                    f"Free cash flow negative in {neg_count} of last "
                    f"{len(valid)} years — cash sustainability concern"
                )
                logger.debug("Flag 6 triggered: FCF negative %d/%d", neg_count, len(valid))
            else:
                logger.debug("Flag 6 not triggered: FCF negative %d/%d", neg_count, len(valid))
    except Exception as exc:
        logger.warning("Flag 6 (negative FCF) check failed: %s", exc)

    # ── Flag 7: Anomalous Earnings Quality (OCF >>> NI) ──────────────────
    try:
        quality = financial_data.get("quality", {})
        is_reit = quality.get("is_reit", False)
        is_bank = quality.get("is_bank", False)
        if not is_reit and not is_bank:
            ocf = financials.get("operating_cash_flow", [])
            ni = financials.get("net_income", [])
            window = min(3, len(ocf), len(ni))
            if window > 0:
                extreme_count = 0
                checked = 0
                for i in range(len(ocf) - window, len(ocf)):
                    if (ocf[i] is not None and ocf[i] > 0
                            and ni[i] is not None and ni[i] != 0):
                        checked += 1
                        if ocf[i] / ni[i] > EARNINGS_QUALITY_HIGH_THRESHOLD:
                            extreme_count += 1
                if checked > 0 and extreme_count >= 1:
                    flags.append(
                        f"Earnings quality anomalous: OCF exceeded net income by "
                        f"more than {EARNINGS_QUALITY_HIGH_THRESHOLD:.0f}x in "
                        f"{extreme_count} of {checked} recent years — investigate "
                        f"non-cash adjustments"
                    )
    except Exception as exc:
        logger.warning("Flag 7 (anomalous earnings quality) check failed: %s", exc)

    # ── Flag 8: Persistent Negative Interest Coverage ────────────────────
    try:
        ebit_series = financials.get("ebit", [])
        interest_series = financials.get("interest_expense", [])
        window = min(3, len(ebit_series), len(interest_series))
        if window > 0:
            neg_count = 0
            checked = 0
            for i in range(len(ebit_series) - window, len(ebit_series)):
                ebit_val = ebit_series[i]
                int_val = interest_series[i]
                if ebit_val is not None and int_val is not None and int_val > 0:
                    checked += 1
                    if ebit_val < int_val:
                        neg_count += 1
            if checked > 0 and neg_count >= 2:
                flags.append(
                    f"EBIT failed to cover interest expense in {neg_count} "
                    f"of {checked} recent years — persistent debt service risk"
                )
    except Exception as exc:
        logger.warning("Flag 8 (negative interest coverage) check failed: %s", exc)

    logger.info("Red flag scan complete: %d flag(s) triggered", len(flags))
    return flags
