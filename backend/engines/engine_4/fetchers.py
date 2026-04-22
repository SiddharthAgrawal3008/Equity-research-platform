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

from backend.engines.shared_config import FMP_API_KEY, SEC_USER_AGENT

logger = logging.getLogger(__name__)

# BOTTLENECK: raise this value to tolerate slow APIs, or lower it to fail fast.
# Each of the three document fetchers waits up to this many seconds independently.
_HTTP_TIMEOUT_S: float = 5.0

# Generic UA for FMP (no special policy). SEC calls use SEC_USER_AGENT instead.
_HTTP_USER_AGENT: str = (
    "Equity-Research-Platform/1.0 (engine_4_nlp)"
)

_FMP_BASE = "https://financialmodelingprep.com/api/v3"
_EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"


def _sec_user_agent_is_placeholder(ua: str) -> bool:
    """True if the configured SEC UA looks like a default/example stub."""
    low = (ua or "").lower()
    return (
        not low.strip()
        or "example.com" in low
        or "@example" in low
        or "todo" in low
        or "replace" in low
    )


# ── HTTP primitives ───────────────────────────────────────────────────

# Module-level snapshot of the most recent HTTP error body (first 200 chars).
# Populated by _http_get on 4xx/5xx so callers can surface the actual server
# response in warnings — crucial for distinguishing "SEC rejected the UA" from
# "corporate proxy blocked the request" since both return 403.
_last_error_body: str = ""


def _http_get(
    url: str,
    timeout: float = _HTTP_TIMEOUT_S,
    extra_headers: dict | None = None,
) -> tuple[int | None, str | None]:
    """Perform a GET and return (status_code, body).

    - On HTTP error (4xx/5xx): returns (status_code, None); error body is
      captured in module-level _last_error_body for diagnostic warnings.
    - On network failure (timeout, DNS, connection refused): returns (None, None).
    - On success: returns (2xx_status, body_text).

    BOTTLENECK: blocking network call — the primary source of wall-time latency
    in Engine 4. Never raises so callers can report precise warnings.
    """
    global _last_error_body
    _last_error_body = ""
    headers = {"User-Agent": _HTTP_USER_AGENT, "Accept": "application/json, */*"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            _last_error_body = exc.read().decode("utf-8", errors="replace")[:200].strip()
        except Exception:
            _last_error_body = ""
        logger.debug("HTTP %s for %s: %s", exc.code, url, _last_error_body)
        return exc.code, None
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        logger.debug("Network error for %s: %s", url, exc)
        return None, None


def _http_get_json(
    url: str,
    timeout: float = _HTTP_TIMEOUT_S,
    extra_headers: dict | None = None,
) -> tuple[int | None, object | None]:
    """Like _http_get but decodes JSON. Returns (status, parsed_or_None)."""
    status, body = _http_get(url, timeout=timeout, extra_headers=extra_headers)
    if body is None:
        return status, None
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, None


def _fetch_with_retry(
    url: str,
    retries: int = 1,
    extra_headers: dict | None = None,
) -> tuple[int | None, str | None]:
    """Retry only on transient network errors (status is None). 4xx are fatal.

    BOTTLENECK: with retries=1, a transient failure doubles the wait time for
    that fetcher (up to 2 × _HTTP_TIMEOUT_S).
    """
    status, body = _http_get(url, extra_headers=extra_headers)
    attempts = 0
    while body is None and status is None and attempts < retries:
        attempts += 1
        status, body = _http_get(url, extra_headers=extra_headers)
    return status, body


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
    status, raw = _fetch_with_retry(url, retries=1)
    if raw is None:
        if status == 401 or status == 403:
            warnings.append(f"FMP returned {status} — check FMP_API_KEY validity")
        elif status is not None:
            warnings.append(f"FMP transcript fetch returned HTTP {status}")
        else:
            warnings.append("FMP transcript fetch failed — network unreachable")
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
    _status, payload = _http_get_json(url)
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


def _edgar_headers() -> dict:
    """Headers required by SEC EDGAR's fair-access policy.

    SEC expects a real User-Agent with contact info; default/placeholder UAs
    may be rate-limited or 403-blocked. Also sets Host and Accept per the
    search-index endpoint's contract.
    """
    return {
        "User-Agent":      SEC_USER_AGENT,
        "Accept":          "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Host":            "efts.sec.gov",
    }


def fetch_edgar_10k(
    ticker: str, warnings: list[str], limit: int = 2,
) -> list[dict]:
    """Search SEC EDGAR full-text search for recent 10-K filings.

    Returns up to `limit` annual_report documents. Full 10-K body text
    extraction is deferred to a later phase; snippet text is used as proxy.

    Graceful failure modes (empty list + specific warning):
        - 403: UA placeholder or SEC block → set SEC_USER_AGENT env var
        - 429: rate-limited by SEC → slow down calling frequency
        - 4xx/5xx: surfaced with status code for debugging
        - network error: unreachable / sandboxed / offline
        - empty hits: ticker has no 10-K on file (valid result)

    NOTE: Only the EDGAR search-index highlight snippet is stored as `text`,
    not the full 10-K filing. This limits red-flag and theme signal from annual
    reports. Fetching and parsing the full filing would improve quality but
    increase both network time and downstream CPU cost significantly.
    """
    if _sec_user_agent_is_placeholder(SEC_USER_AGENT):
        warnings.append(
            "SEC_USER_AGENT is a placeholder — SEC may block requests. "
            "Set SEC_USER_AGENT env var to 'Your Name you@yourdomain.com' "
            "(see https://www.sec.gov/os/accessing-edgar-data)"
        )

    query = urllib.parse.quote(f'"{ticker}" "management discussion"')
    url = f"{_EDGAR_SEARCH}?q={query}&forms=10-K"
    status, payload = _http_get_json(url, extra_headers=_edgar_headers())

    if payload is None:
        body_hint = f" response={_last_error_body!r}" if _last_error_body else ""
        if status == 403:
            warnings.append(
                f"EDGAR returned 403 Forbidden.{body_hint} "
                "Either SEC rejected the User-Agent (set SEC_USER_AGENT to a "
                "real 'Name email@domain' string) OR your network blocks "
                "outbound requests (corporate proxy / sandbox / firewall)."
            )
        elif status == 429:
            warnings.append(
                f"EDGAR returned 429 — rate-limited by SEC (10 req/sec cap).{body_hint} "
                "Reduce call frequency or batch requests."
            )
        elif status is not None:
            warnings.append(
                f"EDGAR search returned HTTP {status}.{body_hint} No annual reports."
            )
        else:
            warnings.append("EDGAR unreachable (network error) — no annual reports")
        return []

    if not isinstance(payload, dict):
        warnings.append("EDGAR search returned non-dict payload — no annual reports")
        return []

    hits = (payload.get("hits") or {}).get("hits") or []
    if not hits:
        warnings.append(f"EDGAR full-text search returned no 10-K hits for {ticker}")
        return []

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
