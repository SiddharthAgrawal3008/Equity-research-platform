"""
pdf_builder.py — Builds an IB-style investment memo PDF using ReportLab.

Instruction 3 changes implemented here:
  1. KPI cover row: "Target" renamed to "DCF Value"
  2. 3-year financial summary table after financial performance narrative
  3. Valuation range table includes current price row
  4. Confidence indicator on cover page next to verdict badge
"""

from __future__ import annotations
import base64
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.engines.engine_5.data_extractor import ReportData
from backend.engines.engine_5.narrative import _fmt_cap, _fmt_m, _fmt_pct, _fmt_price, _fmt_x, _fmt_f

# ── Colour palette ────────────────────────────────────────────────────────────

NAVY        = colors.HexColor("#0A2540")
TEAL        = colors.HexColor("#00B2A9")
LIGHT_GREY  = colors.HexColor("#F4F6F8")
MID_GREY    = colors.HexColor("#8A9BB0")
WHITE       = colors.white
BLACK       = colors.black

VERDICT_COLOURS = {
    "Undervalued":  colors.HexColor("#1DB954"),
    "Fairly Valued": colors.HexColor("#F5A623"),
    "Overvalued":   colors.HexColor("#E84040"),
}
CONFIDENCE_COLOURS = {
    "High":       colors.HexColor("#1DB954"),
    "Medium":     colors.HexColor("#F5A623"),
    "Low":        colors.HexColor("#E84040"),
    "Unreliable": colors.HexColor("#9B59B6"),
}

# ── Style sheet ───────────────────────────────────────────────────────────────

_BASE = getSampleStyleSheet()

STYLE = {
    "title": ParagraphStyle(
        "title", fontSize=22, fontName="Helvetica-Bold",
        textColor=WHITE, spaceAfter=2, leading=26,
    ),
    "subtitle": ParagraphStyle(
        "subtitle", fontSize=11, fontName="Helvetica",
        textColor=MID_GREY, spaceAfter=6,
    ),
    "section_head": ParagraphStyle(
        "section_head", fontSize=13, fontName="Helvetica-Bold",
        textColor=NAVY, spaceBefore=14, spaceAfter=4,
        borderPad=4,
    ),
    "body": ParagraphStyle(
        "body", fontSize=9, fontName="Helvetica",
        textColor=BLACK, leading=13, spaceAfter=4,
    ),
    "kpi_label": ParagraphStyle(
        "kpi_label", fontSize=7, fontName="Helvetica",
        textColor=MID_GREY, alignment=TA_CENTER,
    ),
    "kpi_value": ParagraphStyle(
        "kpi_value", fontSize=12, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
    ),
    "table_header": ParagraphStyle(
        "table_header", fontSize=8, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
    ),
    "table_cell": ParagraphStyle(
        "table_cell", fontSize=8, fontName="Helvetica",
        textColor=BLACK, alignment=TA_RIGHT,
    ),
    "table_label": ParagraphStyle(
        "table_label", fontSize=8, fontName="Helvetica-Bold",
        textColor=NAVY, alignment=TA_LEFT,
    ),
    "badge": ParagraphStyle(
        "badge", fontSize=11, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER,
    ),
    "warning": ParagraphStyle(
        "warning", fontSize=8, fontName="Helvetica-Oblique",
        textColor=MID_GREY, spaceAfter=2,
    ),
}

# ── Helpers ───────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


def _p(text: str, style_key: str = "body") -> Paragraph:
    return Paragraph(str(text).replace("\n", "<br/>"), STYLE[style_key])


def _spacer(h_mm: float = 4) -> Spacer:
    return Spacer(1, h_mm * mm)


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=LIGHT_GREY, spaceAfter=6)


def _section_text(title: str, body: str) -> list:
    """Convert a section title + pre-formatted body string into flowables."""
    flowables = [_p(title, "section_head"), _hr()]
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            flowables.append(_spacer(2))
        elif line.startswith("•"):
            flowables.append(_p(f"&nbsp;&nbsp;&nbsp;{line}", "body"))
        else:
            flowables.append(_p(line, "body"))
    return flowables


# ── Cover page ────────────────────────────────────────────────────────────────

def _cover_page(d: ReportData) -> list:
    """Cover page: dark header band, verdict + confidence badges, KPI strip."""
    story: list = []

    # ── Header band ───────────────────────────────────────────────────
    header_data = [
        [_p(d.company_name, "title")],
        [_p(f"{d.ticker}  ·  {d.sector}  ·  Equity Research  ·  {date.today().strftime('%d %b %Y')}", "subtitle")],
    ]
    header_table = Table(header_data, colWidths=[CONTENT_W])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1,  0), 18),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1,  0), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    story.append(header_table)
    story.append(_spacer(6))

    # ── Verdict badge + Confidence badge (side by side) ───────────────
    # Instruction 3, item 4: confidence badge on cover next to verdict
    verdict    = d.val_verdict    or "N/A"
    confidence = d.val_confidence or "N/A"

    v_colour = VERDICT_COLOURS.get(verdict, MID_GREY)
    c_colour = CONFIDENCE_COLOURS.get(confidence, MID_GREY)

    badge_data = [[
        _p(verdict,              "badge"),
        _p("",                   "badge"),
        _p(f"Confidence: {confidence}", "badge"),
    ]]
    # Column widths must sum to CONTENT_W; centre gap fills the remainder
    badge_col_w = [CONTENT_W * 0.44, CONTENT_W * 0.12, CONTENT_W * 0.44]
    badge_table = Table(badge_data, colWidths=badge_col_w)
    badge_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), v_colour),
        ("BACKGROUND",    (2, 0), (2, 0), c_colour),
        ("BACKGROUND",    (1, 0), (1, 0), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(badge_table)
    story.append(_spacer(8))

    # ── KPI strip ─────────────────────────────────────────────────────
    # "DCF Value" label (renamed from "Target") — Instruction 3, item 1
    kpis = [
        ("Market Cap",   _fmt_cap(d.market_cap)),
        ("TTM Revenue",  _fmt_m(d.ttm_revenue)),
        ("TTM EBITDA",   _fmt_m(d.ttm_ebitda)),
        ("DCF Value",    _fmt_price(d.dcf_value)),    # was "Target"
        ("Current Price", _fmt_price(d.current_price)),
        ("Upside",       _fmt_pct(d.val_upside_pct)),
    ]

    kpi_labels = [[_p(k, "kpi_label") for k, _ in kpis]]
    kpi_values = [[_p(v, "kpi_value") for _, v in kpis]]
    n_kpis     = len(kpis)
    col_w      = CONTENT_W / n_kpis

    kpi_table = Table(kpi_labels + kpi_values, colWidths=[col_w] * n_kpis)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING",    (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("LINEAFTER",     (0, 0), (-2, -1), 0.5, MID_GREY),
    ]))
    story.append(kpi_table)
    story.append(_spacer(10))
    story.append(_hr())

    return story


# ── Financial summary table (3-year trend) ───────────────────────────────────

def _fin_summary_table(d: ReportData) -> list:
    """3-year financial summary table: Year | Revenue | EBITDA | Net Income | FCF.

    Instruction 3, item 2.
    """
    if not d.years:
        return []

    # Take last 3 available years
    pairs = list(zip(d.years, d.revenue, d.ebitda, d.net_income, d.fcf))
    pairs = [(y, r, e, ni, f) for y, r, e, ni, f in pairs][-3:]
    if not pairs:
        return []

    header = ["Year", "Revenue", "EBITDA", "Net Income", "FCF"]
    rows   = [header]
    for y, r, e, ni, f in pairs:
        rows.append([
            str(y),
            _fmt_m(r),
            _fmt_m(e),
            _fmt_m(ni),
            _fmt_m(f),
        ])

    col_w = [CONTENT_W / len(header)] * len(header)
    tbl   = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [_p("3-Year Financial Summary", "section_head"), tbl, _spacer(6)]


# ── Valuation range table ─────────────────────────────────────────────────────

def _val_range_table(d: ReportData) -> list:
    """Valuation range table with current price included — Instruction 3, item 3."""
    rows = [
        ["Metric", "Value"],
        ["Current Price",   _fmt_price(d.current_price)],
        ["DCF Value",       _fmt_price(d.dcf_value)],
        ["Range — Low",     _fmt_price(d.val_range_low)],
        ["Range — Mid",     _fmt_price(d.val_range_mid)],
        ["Range — High",    _fmt_price(d.val_range_high)],
        ["Implied Upside",  _fmt_pct(d.val_upside_pct)],
    ]
    if d.wacc is not None:
        rows.append(["WACC", _fmt_pct(d.wacc)])
    if d.terminal_growth_rate is not None:
        rows.append(["Terminal Growth", _fmt_pct(d.terminal_growth_rate)])
    if d.terminal_value_pct is not None:
        rows.append(["Terminal Value / EV", _fmt_pct(d.terminal_value_pct)])

    col_w = [CONTENT_W * 0.55, CONTENT_W * 0.45]
    tbl   = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        # Highlight current price row
        ("BACKGROUND",    (0, 1), (-1, 1), colors.HexColor("#EAF4FF")),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return [_p("Valuation Summary Table", "section_head"), tbl, _spacer(6)]


def _relative_val_table(d: ReportData) -> list:
    """Peer comparison table for EV/EBITDA, P/E, P/B."""
    rows = [
        ["Multiple", "Company", "Peers Median"],
        ["EV/EBITDA", _fmt_x(d.ev_ebitda_company), _fmt_x(d.ev_ebitda_peers)],
        ["P/E",       _fmt_x(d.pe_company),        _fmt_x(d.pe_peers)],
        ["P/B",       _fmt_x(d.pb_company),        _fmt_x(d.pb_peers)],
    ]
    col_w = [CONTENT_W / 3] * 3
    tbl   = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [_p("Relative Valuation vs Peers", "section_head"), tbl, _spacer(6)]


# ── Main builder ──────────────────────────────────────────────────────────────

def build_pdf(d: ReportData, sections: dict[str, str], warnings: list[str]) -> bytes:
    """Render the full investment memo to PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title=f"{d.ticker} — Investment Memo",
        author="Equity Research Platform",
    )

    story: list = []

    # ── Cover ─────────────────────────────────────────────────────────
    story += _cover_page(d)

    # ── Section 1: Business Summary ───────────────────────────────────
    if "business_summary" in sections:
        story += _section_text("1. Business Summary", sections["business_summary"])
        story.append(_spacer(4))

    # ── Section 2: Financial Performance ─────────────────────────────
    if "financial_performance" in sections:
        story += _section_text("2. Financial Performance Overview", sections["financial_performance"])
        story += _fin_summary_table(d)          # 3-year table after narrative
        story.append(_spacer(4))

    story.append(PageBreak())

    # ── Section 3: Valuation Range ────────────────────────────────────
    if "valuation_range" in sections:
        story += _section_text("3. Valuation Range", sections["valuation_range"])
        story += _val_range_table(d)            # table with current price
        if any(x is not None for x in [d.ev_ebitda_company, d.pe_company, d.pb_company]):
            story += _relative_val_table(d)
        story.append(_spacer(4))

    # ── Section 4: Key Risks ──────────────────────────────────────────
    if "key_risks" in sections:
        story += _section_text("4. Key Risks", sections["key_risks"])
        story.append(_spacer(4))

    story.append(PageBreak())

    # ── Section 5: Investment Thesis ──────────────────────────────────
    if "investment_thesis" in sections:
        story += _section_text("5. Investment Thesis", sections["investment_thesis"])
        story.append(_spacer(4))

    # ── Section 6: Bear Case ──────────────────────────────────────────
    if "bear_case" in sections:
        story += _section_text("6. Bear Case", sections["bear_case"])
        story.append(_spacer(4))

    # ── Warnings footer ───────────────────────────────────────────────
    if warnings:
        story.append(_hr())
        story.append(_p("Notes & Warnings", "section_head"))
        for w in warnings:
            story.append(_p(f"• {w}", "warning"))

    doc.build(story)
    return buf.getvalue()


def build_pdf_base64(d: ReportData, sections: dict[str, str], warnings: list[str]) -> str:
    """Return the PDF as a base64-encoded string."""
    return base64.b64encode(build_pdf(d, sections, warnings)).decode("utf-8")
