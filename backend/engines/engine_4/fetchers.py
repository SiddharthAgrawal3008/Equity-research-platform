"""
Engine 4 — External Document Fetchers
======================================
HTTP helpers + FMP / SEC EDGAR fetchers.
All failures are swallowed; callers receive [] and a warning string.
Uses only stdlib (urllib) — no new dependencies.
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from backend.engines.shared_config import FMP_API_KEY

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT_S: float = 5.0
_HTTP_USER_AGENT: str = (
    "Equity-Research-Platform/1.0 (engine_4_nlp; contact: team@example.com)"
)

_FMP_BASE = "https://financialmodelingprep.com/api/v3"
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"


# ── HTTP primitives ───────────────────────────────────────────────────

def _http_get(url: str, timeout: float = _HTTP_TIMEOUT_S) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": _HTTP_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, OSError) as exc:
        logger.debug("HTTP GET failed for %s: %s", url, exc)
        return None


def _http_get_json(url: str, timeout: float = _HTTP_TIMEOUT_S):
    raw = _http_get(url, timeout=timeout)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _fetch_with_retry(url: str, retries: int = 1) -> str | None:
    result = _http_get(url)
    attempts = 0
    while result is None and attempts < retries:
        attempts += 1
        result = _http_get(url)
    return result


def _fmp_enabled() -> bool:
    key = (FMP_API_KEY or "").strip()
    if not key:
        return False
    return key.upper() not in {"YOUR_FMP_API_KEY_HERE", "REPLACE_ME", "TODO"}


def _coerce_iso_date(raw: str) -> str:
    """Normalize a date string to ISO 8601 (YYYY-MM-DD). Returns '' on failure."""
    if not raw or not isinstance(raw, str):
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%Y/%m/%d", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


# ── Document fetchers ─────────────────────────────────────────────────

def fetch_fmp_transcripts(
    ticker: str, warnings: list[str], limit: int = 8,
) -> list[dict]:
    """Fetch up to `limit` earnings call transcripts from FMP.

    Each returned document dict has:
        doc_type, period, date, source_url, word_count, text, quarter, year.
    Returns [] and appends a warning on any failure.
    """
    if not _fmp_enabled():
        warnings.append("FMP_API_KEY not configured — skipping earnings transcripts")
        return []

    url = (
        f"{_FMP_BASE}/earning_call_transcript/"
        f"{urllib.parse.quote(ticker)}"
        f"?apikey={urllib.parse.quote(FMP_API_KEY)}&limit={int(limit)}"
    )
    raw = _fetch_with_retry(url, retries=1)
    if raw is None:
        warnings.append("FMP transcript fetch failed — proceeding without transcripts")
        return []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        warnings.append("FMP transcript response was not JSON")
        return []

    if not isinstance(payload, list):
        return []

    out: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            continue
        quarter = item.get("quarter")
        year = item.get("year")
        date_str = item.get("date") or ""
        iso_date = _coerce_iso_date(date_str)
        period = f"Q{quarter} {year}" if quarter and year else (iso_date or "unknown")
        out.append({
            "doc_type":   "earnings_transcript",
            "period":     period,
            "date":       iso_date,
            "source_url": None,
            "word_count": len(text.split()),
            "text":       text,
            "quarter":    quarter,
            "year":       year,
        })
    out.sort(key=lambda d: d["date"] or "")
    return out


def fetch_fmp_press_releases(
    ticker: str, warnings: list[str], limit: int = 4,
) -> list[dict]:
    """Fetch press releases from FMP. Silent on failure (supplementary source)."""
    if not _fmp_enabled():
        return []
    url = (
        f"{_FMP_BASE}/press-releases/"
        f"{urllib.parse.quote(ticker)}"
        f"?apikey={urllib.parse.quote(FMP_API_KEY)}&limit={int(limit)}"
    )
    payload = _http_get_json(url)
    if not isinstance(payload, list):
        return []

    out: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content") or ""
        if not isinstance(text, str) or not text.strip():
            continue
        iso_date = _coerce_iso_date(item.get("date") or "")
        out.append({
            "doc_type":   "press_release",
            "period":     iso_date or "unknown",
            "date":       iso_date,
            "source_url": item.get("url"),
            "word_count": len(text.split()),
            "text":       text,
        })
    out.sort(key=lambda d: d["date"] or "")
    return out


def fetch_edgar_10k(
    ticker: str, warnings: list[str], limit: int = 2,
) -> list[dict]:
    """Search SEC EDGAR full-text search for recent 10-K filings.

    Returns up to `limit` annual_report documents. Full 10-K body text
    extraction is deferred to a later phase; snippet text is used as proxy.
    """
    query = urllib.parse.quote(f'"{ticker}" "management discussion"')
    url = f"{_EDGAR_SEARCH}?q={query}&forms=10-K"
    payload = _http_get_json(url)
    if not isinstance(payload, dict):
        warnings.append("EDGAR search unavailable — no annual reports fetched")
        return []

    hits = (payload.get("hits") or {}).get("hits") or []
    out: list[dict] = []
    for hit in hits[:limit]:
        if not isinstance(hit, dict):
            continue
        src = hit.get("_source") or {}
        iso_date = _coerce_iso_date(src.get("file_date") or "")
        accession = (hit.get("_id") or "").split(":")[0]
        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/?accession={accession}"
            if accession else
            f"https://www.sec.gov/cgi-bin/browse-edgar?"
            f"action=getcompany&CIK={urllib.parse.quote(ticker)}&type=10-K"
        )
        period = f"FY{iso_date[:4]}" if iso_date else "unknown"
        snippet_text = " ".join(
            s for s in (hit.get("highlight") or {}).get("text", [])
            if isinstance(s, str)
        )
        out.append({
            "doc_type":   "annual_report",
            "period":     period,
            "date":       iso_date,
            "source_url": doc_url,
            "word_count": len(snippet_text.split()),
            "text":       snippet_text,
        })
    out.sort(key=lambda d: d["date"] or "")
    return out


# Private aliases kept for backward compatibility with any code that
# imported the leading-underscore names from engine_4_nlp.py.
_fetch_fmp_transcripts    = fetch_fmp_transcripts
_fetch_fmp_press_releases = fetch_fmp_press_releases
_fetch_edgar_10k          = fetch_edgar_10k
