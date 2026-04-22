"""
Engine 4 — Word Lists & Markers
================================
Finance-domain lexicons for rule-based sentiment scoring.
Expand entries without touching any scoring logic.

PERFORMANCE NOTE: POSITIVE_WORDS, RISK_WORDS, and HEDGING_WORDS are checked via
set membership (`in`) per token — O(1) per lookup, so expanding these sets has
negligible CPU cost. GUIDANCE_MARKERS and QNA_MARKERS use str.find on full text;
adding more markers increases the guidance-scoring loop in _score_block linearly.
"""

POSITIVE_WORDS: set[str] = {
    "growth", "strong", "excellent", "record", "improve", "improved",
    "improving", "confident", "confidence", "momentum", "success", "successful",
    "robust", "accelerate", "accelerating", "beat", "outperform", "outperformed",
    "expansion", "expand", "innovation", "leadership", "advantage", "profitable",
    "profitability", "efficient", "efficiency", "exceeded", "gain", "gains",
    "positive", "opportunity", "opportunities", "upside", "resilient", "solid",
    "healthy", "achievement", "milestone", "breakthrough", "optimistic",
}

RISK_WORDS: set[str] = {
    "risk", "risks", "uncertainty", "uncertainties", "volatile", "volatility",
    "decline", "declining", "declined", "weakness", "weaken", "weakening",
    "pressure", "challenge", "challenges", "challenging", "headwind",
    "headwinds", "difficult", "difficulty", "unfavorable", "slowdown",
    "recession", "litigation", "investigation", "lawsuit", "breach",
    "impairment", "restructuring", "layoff", "layoffs", "warning", "shortfall",
    "miss", "missed", "adverse", "deteriorate", "deteriorating", "downturn",
    "loss", "losses", "disrupt", "disruption", "shortage", "shortages",
}

HEDGING_WORDS: set[str] = {
    "may", "might", "could", "possibly", "potentially", "approximately",
    "somewhat", "uncertain", "likely", "estimate", "estimates", "assume",
    "assumption", "believe", "anticipate", "anticipated", "roughly",
    "contingent", "approximate", "perhaps", "expected", "expects",
    "projected", "intend", "intends", "seek",
}

# Markers used to split prepared remarks from Q&A in earnings call transcripts.
# Case-insensitive substring match on the transcript body.
QNA_MARKERS: tuple[str, ...] = (
    "question-and-answer session",
    "question and answer session",
    "we will now begin the question",
    "open the call for questions",
    "our first question comes",
    "move to the q&a",
    "begin our q&a",
)

# Markers that indicate forward guidance remarks.
GUIDANCE_MARKERS: tuple[str, ...] = (
    "guidance", "outlook", "expect", "we anticipate", "fiscal year",
    "next quarter", "full year", "forward",
)
