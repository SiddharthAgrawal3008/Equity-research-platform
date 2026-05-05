import os
import json
import logging
from dotenv import load_dotenv
from groq import Groq
from backend.pipeline.orchestrator import run_pipeline
from backend.engines import DEFAULT_ENGINES

load_dotenv()
logger = logging.getLogger(__name__)

_api_key = os.getenv("GROK_API_KEY")
if not _api_key:
    raise RuntimeError("GROK_API_KEY must be set in .env")

client = Groq(api_key=_api_key)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an equity research assistant for a financial analysis platform. You have two capabilities:

1. DIRECT ANSWERS: For general finance questions (what is DCF, explain WACC, compare PE vs EV/EBITDA, etc.), answer directly from your knowledge. Be concise, accurate, and practical.

2. STOCK ANALYSIS: When a user asks to analyze, value, or research a specific stock/company, call the run_analysis tool with the ticker symbol. After receiving the results, provide a conversational summary highlighting:
   - Valuation verdict and confidence level
   - Key risk metrics and any red flags
   - Notable strengths and concerns
   - The overall investment thesis in plain language

When summarizing analysis results:
- Lead with the verdict (undervalued/overvalued/fairly valued) and confidence
- Mention specific numbers (intrinsic value, current price, upside %)
- Flag any warnings or data quality issues honestly
- If confidence is "Low" or "Unreliable", say so clearly and explain why
- Keep it conversational — you're a knowledgeable analyst talking to a colleague, not generating a formal report

Do NOT make up financial data. If you don't have analysis results, say so.
Do NOT call run_analysis unless the user specifically asks about a stock/company.
If the user gives a company name instead of a ticker, infer the ticker (e.g., "Apple" → "AAPL").
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_analysis",
            "description": (
                "Run a full equity research analysis on a stock ticker. "
                "Use this when the user asks to analyze, value, or research "
                "a specific company or stock. Returns financial data, "
                "valuation (DCF + relative), risk metrics, NLP insights, "
                "and a structured report."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL, TSLA, MSFT",
                    }
                },
                "required": ["ticker"],
            },
        },
    }
]


def _summarize_context(context: dict) -> str:
    ticker = context.get("ticker", "")
    status = context.get("status", {})
    errors = context.get("errors", [])

    val = context.get("valuation", {})
    val_summary = val.get("summary", {})
    dcf = val.get("dcf", {})
    relative = val.get("relative", {})
    val_range = val.get("valuation_range", {})
    val_meta = val.get("meta", {})

    risk = context.get("risk_metrics", {})
    beta_obj = risk.get("beta", {})
    mkt_risk = risk.get("market_risk", {})
    fin_health = risk.get("financial_health", {})
    red_flags = risk.get("red_flags", [])

    nlp = context.get("nlp_insights", {})

    summary = {
        "ticker": ticker,
        "engine_status": status,
        "errors": errors,
        "valuation": {
            "verdict": val_summary.get("verdict"),
            "confidence": val_summary.get("confidence"),
            "current_price": val_summary.get("current_price"),
            "dcf_intrinsic_value": dcf.get("intrinsic_value_per_share"),
            "dcf_status": dcf.get("status"),
            "dcf_wacc": dcf.get("wacc"),
            "dcf_upside_pct": dcf.get("upside_pct"),
            "relative_status": relative.get("status"),
            "pe_company": relative.get("pe_company"),
            "pe_peers_median": relative.get("pe_peers_median"),
            "pe_implied_value": relative.get("pe_implied_value"),
            "ev_ebitda_company": relative.get("ev_ebitda_company"),
            "valuation_range": val_range,
            "warnings": val_meta.get("warnings", []),
        },
        "risk": {
            "beta": beta_obj.get("value"),
            "beta_source": beta_obj.get("source"),
            "volatility": mkt_risk.get("historical_volatility"),
            "sharpe_ratio": mkt_risk.get("sharpe_ratio"),
            "max_drawdown": mkt_risk.get("max_drawdown"),
            "var_95_daily": mkt_risk.get("var_95_daily"),
            "altman_z_score": fin_health.get("altman_z_score"),
            "altman_z_zone": fin_health.get("altman_z_zone"),
            "interest_coverage": fin_health.get("interest_coverage"),
            "debt_to_ebitda": fin_health.get("debt_to_ebitda"),
            "current_ratio": fin_health.get("current_ratio"),
            "debt_to_equity": fin_health.get("debt_to_equity"),
            "earnings_quality": fin_health.get("earnings_quality"),
            "red_flags": red_flags,
        },
        "nlp": {
            "sentiment_score": (nlp.get("sentiment") or {}).get("overall_score"),
            "red_flags": nlp.get("red_flags", []),
            "key_themes": nlp.get("key_themes", []),
        },
    }
    return json.dumps(summary, indent=2, default=str)


def chat(message: str, history: list[dict]) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3,
        max_tokens=4096,
    )

    choice = response.choices[0]
    tool_used = None
    ticker_analyzed = None
    analysis_data = None

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        tool_call = choice.message.tool_calls[0]
        if tool_call.function.name == "run_analysis":
            args = json.loads(tool_call.function.arguments)
            ticker = args.get("ticker", "").upper().strip()

            if not ticker:
                return {
                    "reply": "I need a ticker symbol to run the analysis. What stock would you like me to analyze?",
                    "tool_used": None,
                    "ticker_analyzed": None,
                    "analysis_data": None,
                }

            logger.info(f"LLM requested analysis for {ticker}")
            tool_used = "run_analysis"
            ticker_analyzed = ticker

            try:
                context = run_pipeline(ticker, DEFAULT_ENGINES)
                analysis_data = context
                context_summary = _summarize_context(context)
            except Exception as exc:
                logger.exception(f"Pipeline failed for {ticker}")
                return {
                    "reply": f"I tried to analyze {ticker} but the pipeline encountered an error: {exc}. This could be due to the ticker being invalid or a data source being temporarily unavailable.",
                    "tool_used": "run_analysis",
                    "ticker_analyzed": ticker,
                    "analysis_data": None,
                }

            followup_messages = messages + [
                {"role": "assistant", "content": None, "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": "run_analysis",
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ]},
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": context_summary,
                },
            ]

            followup = client.chat.completions.create(
                model=MODEL,
                messages=followup_messages,
                temperature=0.3,
                max_tokens=4096,
            )

            return {
                "reply": followup.choices[0].message.content or "Analysis complete but I couldn't generate a summary.",
                "tool_used": tool_used,
                "ticker_analyzed": ticker_analyzed,
                "analysis_data": analysis_data,
            }

    return {
        "reply": choice.message.content or "I'm not sure how to respond to that. Could you rephrase?",
        "tool_used": None,
        "ticker_analyzed": None,
        "analysis_data": None,
    }
