"""
Chat route — LLM-powered follow-up Q&A on analysis results.
=============================================================
POST /api/chat  {"question": "...", "analysis_context": {...}}
    → Sends question + analysis summary to Groq
    → Returns LLM response
"""

import os
import json
import logging
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class ChatRequest(BaseModel):
    question: str
    analysis_context: dict | None = None


def _build_context_summary(ctx: dict) -> str:
    """Build a concise text summary of the analysis for the LLM."""
    if not ctx:
        return "No analysis context available."

    parts = []

    # Company info
    fd = ctx.get("financial_data", {})
    meta = fd.get("meta", {})
    if meta.get("company_name"):
        parts.append(f"Company: {meta['company_name']} ({meta.get('ticker', '?')})")
        parts.append(f"Sector: {meta.get('sector', '?')} | Price: ${meta.get('current_price', '?')}")

    # TTM
    ttm = fd.get("ttm", {})
    if ttm.get("revenue"):
        parts.append(f"TTM Revenue: ${ttm['revenue']:.0f}M | EBITDA: ${ttm.get('ebitda', 0):.0f}M | Net Income: ${ttm.get('net_income', 0):.0f}M | FCF: ${ttm.get('free_cash_flow', 0):.0f}M")

    # Valuation
    val = ctx.get("valuation", {})
    summary = val.get("summary", {})
    dcf = val.get("dcf", {})
    if summary.get("verdict"):
        parts.append(f"Valuation Verdict: {summary['verdict']} | Confidence: {summary.get('confidence', '?')}")
    if dcf.get("intrinsic_value_per_share"):
        parts.append(f"DCF Value: ${dcf['intrinsic_value_per_share']:.2f} | WACC: {dcf.get('wacc', 0)*100:.1f}% | Terminal Growth: {dcf.get('terminal_growth_rate', 0)*100:.1f}%")
        parts.append(f"Terminal Value %: {dcf.get('terminal_value_pct', 0)*100:.1f}%")

    rel = val.get("relative", {})
    if rel.get("pe_company"):
        parts.append(f"PE: {rel['pe_company']:.1f} (peers: {rel.get('pe_peers_median', '?')}) | PB: {rel.get('pb_company', '?')}")

    rev_dcf = val.get("reverse_dcf", {})
    if rev_dcf.get("implied_growth_rate") is not None:
        parts.append(f"Reverse DCF implied growth: {rev_dcf['implied_growth_rate']*100:.2f}% | Market stance: {rev_dcf.get('market_implied_stance', '?')}")

    # Risk
    risk = ctx.get("risk_metrics", {})
    mr = risk.get("market_risk", {})
    fh = risk.get("financial_health", {})
    if fh.get("altman_z_score"):
        parts.append(f"Altman Z: {fh['altman_z_score']:.2f} ({fh.get('altman_z_zone', '?')}) | Beta: {mr.get('beta', mr.get('beta_value', '?'))} | Sharpe: {mr.get('sharpe_ratio', '?')}")
        parts.append(f"Interest Coverage: {fh.get('interest_coverage', '?')} | Debt/EBITDA: {fh.get('debt_to_ebitda', '?')} | Current Ratio: {fh.get('current_ratio', '?')}")
    if mr.get("max_drawdown"):
        parts.append(f"Max Drawdown: {mr['max_drawdown']*100:.1f}% | VaR 95%: {mr.get('var_95', mr.get('var_95_daily', '?'))}")

    # NLP
    nlp = ctx.get("nlp_insights", {})
    sent = nlp.get("sentiment", {})
    if sent.get("overall_score") is not None:
        parts.append(f"NLP Sentiment: {sent['overall_score']:.3f} ({sent.get('label', '?')})")
    themes = nlp.get("key_themes", {})
    if themes.get("themes"):
        parts.append(f"Key Themes: {', '.join(themes['themes'][:6])}")
    alignment = themes.get("financial_alignment", {})
    if alignment:
        parts.append(f"Financial Alignment: {'Aligned' if alignment.get('aligned') else 'DIVERGENCE detected'}")

    # Red flags
    flags = risk.get("red_flags", [])
    if not isinstance(flags, list):
        flags = []
    nlp_flags = nlp.get("red_flags", [])
    if not isinstance(nlp_flags, list):
        nlp_flags = []
    all_flags = flags + nlp_flags
    if all_flags:
        flag_texts = [f.get("flag", f.get("message", str(f))) for f in all_flags[:5]]
        parts.append(f"Red Flags ({len(all_flags)}): {'; '.join(flag_texts)}")

    # Warnings
    warnings = val.get("meta", {}).get("warnings", [])
    if warnings:
        parts.append(f"Valuation Warnings: {'; '.join(warnings[:3])}")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are EquiMind's financial research assistant. You have access to a complete equity analysis that was just run by the platform's 5-engine pipeline.

Your job is to answer follow-up questions about the analysis clearly and accurately. You should:
- Reference specific numbers from the analysis when relevant
- Explain methodology (DCF, relative valuation, risk metrics) when asked
- Be honest about limitations and confidence levels
- Use plain language but maintain analytical rigor
- Keep answers concise but thorough

You are NOT giving investment advice. You are explaining the analysis that was computed.

Here is the complete analysis context:
{context}"""


@router.post("/chat")
def chat_endpoint(request: ChatRequest) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    context_summary = _build_context_summary(request.analysis_context or {})

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(context=context_summary),
                    },
                    {
                        "role": "user",
                        "content": request.question,
                    },
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} {response.text}")
            raise HTTPException(status_code=502, detail=f"LLM API error: {response.status_code}")

        data = response.json()
        answer = data["choices"][0]["message"]["content"]

        return {"answer": answer, "model": GROQ_MODEL}

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="LLM request timed out")
    except Exception as exc:
        logger.exception("Chat endpoint failed")
        raise HTTPException(status_code=500, detail=str(exc))
