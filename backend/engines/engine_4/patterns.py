"""
Engine 4 — Red-Flag Patterns & Theme Keywords
==============================================
Static pattern dictionaries used by analysis.py.
"""

VALID_CATEGORIES: list[str] = [
    "supply_chain",
    "guidance_decline",
    "litigation",
    "margin_pressure",
    "competition",
    "regulatory",
    "macro_exposure",
]

# Minimum total hits across all docs for a category to fire.
CATEGORY_MIN_HITS: int = 2

# PERFORMANCE NOTE: every pattern string in RED_FLAG_PATTERNS and every keyword
# in THEME_KEYWORDS is matched via str.find across every document in analysis.py.
# Adding more patterns / keywords increases CPU cost linearly — keep lists lean.

RED_FLAG_PATTERNS: dict[str, tuple[str, ...]] = {
    "supply_chain": (
        "supply chain", "disruption", "shortage", "bottleneck",
        "logistics", "inventory build", "component shortage",
    ),
    "guidance_decline": (
        "lower guidance", "reducing outlook", "revised downward",
        "cut guidance", "withdrew guidance", "lowering guidance",
        "below guidance", "reduced forecast", "guided lower",
    ),
    "litigation": (
        "lawsuit", "litigation", "plaintiff", "class action",
        "settlement", "fine", "penalty", "regulatory action",
        "consent decree", "subpoena",
    ),
    "margin_pressure": (
        "margin pressure", "cost inflation", "input cost",
        "pricing pressure", "margin compression",
        "gross margin decline", "gross margin decrease", "cost pressure",
    ),
    "competition": (
        "competitive pressure", "market share loss",
        "losing share", "new entrant", "competitor", "price war",
        "increased competition",
    ),
    "regulatory": (
        "regulatory", "compliance risk", "new regulation",
        "regulatory scrutiny", "sec inquiry", "policy change",
        "antitrust",
    ),
    "macro_exposure": (
        "inflation", "recession", "interest rate", "currency headwind",
        "fx headwind", "economic slowdown", "geopolitical",
        "commodity price",
    ),
}

FLAG_TEMPLATES: dict[str, str] = {
    "supply_chain":     "Supply chain disruption language detected",
    "guidance_decline": "Guidance reduction language detected",
    "litigation":       "Litigation / regulatory action exposure",
    "margin_pressure":  "Margin pressure / cost inflation concerns",
    "competition":      "Competitive pressure or market share loss",
    "regulatory":       "Regulatory / compliance risk mentions",
    "macro_exposure":   "Macro headwind exposure (inflation, FX, rates)",
}

THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "AI / Machine Learning": (
        "artificial intelligence", "machine learning", "generative",
        " ai ", " ai,", " ai.", " llm", "large language model",
        "neural network",
    ),
    "Cloud / SaaS": (
        "cloud", "saas", "software as a service", "platform",
        "infrastructure as a service", " paas",
    ),
    "Services / Recurring Revenue": (
        "services revenue", "subscription", "recurring revenue",
        "annual recurring", "arr",
    ),
    "International Expansion": (
        "international", "overseas", "global market", "emerging market",
        " china", " europe", " india", " japan",
    ),
    "Capital Returns": (
        "dividend", "buyback", "share repurchase", "return capital",
        "capital return",
    ),
    "Margin Expansion": (
        "margin expansion", "operating leverage", "margin improvement",
        "gross margin expansion",
    ),
    "Revenue Growth": (
        "revenue growth", "top-line growth", "topline", "top line growth",
        "sales growth",
    ),
    "Product Innovation": (
        "innovation", "new product", "product launch", "r&d investment",
        "research and development", "product pipeline",
    ),
    "Cost Discipline / Efficiency": (
        "cost discipline", "cost efficiency", "productivity",
        "cost reduction", "operating efficiency", "restructuring savings",
    ),
}
