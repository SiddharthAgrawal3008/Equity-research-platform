import type { CompanyData, Rating, RiskLevel } from "./mockData";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ── Fetch ────────────────────────────────────────────────────────────────────

export async function fetchResearch(
  ticker: string,
  financialOverride?: Record<string, unknown>,
): Promise<CompanyData> {
  const res = await fetch(`${BASE_URL}/api/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ticker: ticker.toUpperCase(),
      ...(financialOverride ? { financial_override: financialOverride } : {}),
    }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const ctx = await res.json();
  return mapPipelineToCompanyData(ctx);
}

// ── Mapper ───────────────────────────────────────────────────────────────────
// Converts the backend pipeline context (5-engine data bus) → CompanyData
// Fields the backend doesn't yet produce (description, change, eps, etc.)
// fall back to sensible placeholders so the UI never crashes.

function mapPipelineToCompanyData(ctx: Record<string, unknown>): CompanyData {
  const fd = (ctx.financial_data ?? {}) as Record<string, unknown>;
  const val = (ctx.valuation ?? {}) as Record<string, unknown>;
  const risk = (ctx.risk_metrics ?? {}) as Record<string, unknown>;
  const nlp = (ctx.nlp_insights ?? {}) as Record<string, unknown>;
  const report = (ctx.report ?? {}) as Record<string, unknown>;

  // financial_data sub-objects
  const meta = (fd.meta ?? {}) as Record<string, unknown>;
  const mktData = (fd.market_data ?? {}) as Record<string, unknown>;
  const fins = (fd.financials ?? {}) as Record<string, unknown>;

  // valuation sub-objects
  const dcf = (val.dcf ?? {}) as Record<string, unknown>;
  const relative = (val.relative ?? {}) as Record<string, unknown>;
  const sensitivity = (val.sensitivity ?? {}) as Record<string, unknown>;
  const valRange = (val.valuation_range ?? {}) as Record<string, unknown>;
  const summary = (val.summary ?? {}) as Record<string, unknown>;

  // risk sub-objects
  const betaObj = (risk.beta ?? {}) as Record<string, unknown>;
  const mktRisk = (risk.market_risk ?? {}) as Record<string, unknown>;
  const health = (risk.financial_health ?? {}) as Record<string, unknown>;

  // ── Basic info ──────────────────────────────────────────────────────
  const ticker = String(ctx.ticker ?? "");
  const name = String(meta.company_name ?? ticker);
  const sector = String(meta.sector ?? "—");
  const industry = String(meta.industry ?? "—");
  const marketCapRaw = Number(meta.market_cap ?? mktData.market_cap ?? 0);
  const marketCap = marketCapRaw ? `$${(marketCapRaw / 1e6).toFixed(2)}T` : "—";
  const price = Number(mktData.current_price ?? meta.current_price ?? 0);

  // ── Rating from valuation summary verdict ───────────────────────────
  const verdictRaw = String(summary.verdict ?? "").toUpperCase();
  const rating: Rating = verdictRaw === "UNDERVALUED"
    ? "BUY"
    : verdictRaw === "OVERVALUED"
    ? "SELL"
    : "HOLD";

  // ── Valuation ───────────────────────────────────────────────────────
  const intrinsicValue = Number(dcf.intrinsic_value_per_share ?? 0);
  const upside = Number(dcf.upside_pct ?? 0);
  const wacc = Number(dcf.wacc ?? 0);
  const terminalGrowth = Number(dcf.terminal_growth_rate ?? 0);

  // ── Stats row ───────────────────────────────────────────────────────
  const revenueArr = Array.isArray(fins.revenue) ? (fins.revenue as number[]) : [];
  const latestRevenue = revenueArr.at(-1) ?? 0;
  const netIncomeArr = Array.isArray(fins.net_income) ? (fins.net_income as number[]) : [];
  const latestNI = netIncomeArr.at(-1) ?? 0;
  const sharesOut = Number(mktData.shares_outstanding ?? 15000);
  const eps = sharesOut > 0 ? (latestNI / sharesOut).toFixed(2) : "—";
  const peCalc = price > 0 && sharesOut > 0 && latestNI > 0
    ? (price / (latestNI / sharesOut)).toFixed(1)
    : "—";
  const evEbitda = typeof relative.ev_ebitda_company === "number"
    ? relative.ev_ebitda_company.toFixed(1)
    : "—";

  const stats = {
    revenue: latestRevenue ? `$${(latestRevenue / 1e3).toFixed(1)}B` : "—",
    eps: eps !== "—" ? `$${eps}` : "—",
    pe: peCalc !== "—" ? `${peCalc}x` : "—",
    evEbitda: evEbitda !== "—" ? `${evEbitda}x` : "—",
  };

  // ── Peers ───────────────────────────────────────────────────────────
  type PeerRaw = Record<string, unknown>;
  const peersRaw = Array.isArray(relative.peers) ? (relative.peers as PeerRaw[]) : [];
  const peers = peersRaw.map((p) => ({
    ticker: String(p.ticker ?? p.symbol ?? ""),
    pe: Number(p.pe ?? p.pe_ratio ?? 0),
    ev: Number(p.ev_ebitda ?? p.ev ?? 0),
    pb: Number(p.pb ?? p.pb_ratio ?? 0),
  }));

  // ── Sensitivity matrix (5×5) ────────────────────────────────────────
  const rawMatrix = Array.isArray(sensitivity.value_matrix)
    ? (sensitivity.value_matrix as number[][])
    : [];
  const sensitivityMatrix: number[][] =
    rawMatrix.length >= 5
      ? rawMatrix.slice(0, 5).map((row) =>
          Array.isArray(row) ? row.slice(0, 5).map(Number) : [0, 0, 0, 0, 0],
        )
      : Array.from({ length: 5 }, (_, r) =>
          Array.from({ length: 5 }, (_, c) =>
            +(intrinsicValue * (0.85 + r * 0.07 + c * 0.02)).toFixed(1),
          ),
        );

  // ── Monte Carlo distribution ────────────────────────────────────────
  // Backend doesn't expose raw MC distribution yet — derive bell curve
  // from valuation_range {low, mid, high}.
  const mcMid = Number(valRange.mid ?? intrinsicValue);
  const mcSpan = Math.abs(Number(valRange.high ?? mcMid * 1.2) - mcMid) || mcMid * 0.2;
  const monteCarlo = Array.from({ length: 25 }, (_, i) => {
    const x = mcMid - mcSpan + (i * (mcSpan * 2)) / 24;
    const z = (x - mcMid) / (mcSpan / 2.5);
    return { v: +x.toFixed(1), freq: +(Math.exp(-(z * z) / 2) * 100).toFixed(1) };
  });

  // ── Risk ────────────────────────────────────────────────────────────
  const beta = Number(betaObj.value ?? 1);
  const sharpe = Number(mktRisk.sharpe_ratio ?? 0);
  const maxDrawdown = Number(mktRisk.max_drawdown ?? 0);
  const var95 = Number(mktRisk.var_95_daily ?? 0);
  const altmanZ = Number(health.altman_z_score ?? 0);
  const debtToEquity = Number(health.debt_to_equity ?? 0);
  const interestCoverage = Number(health.interest_coverage ?? 0);
  const currentRatio = Number(health.current_ratio ?? 0);

  const riskLevel: RiskLevel =
    beta > 1.5 || altmanZ < 1.8 ? "High" : beta < 0.8 && altmanZ > 3 ? "Low" : "Medium";

  // ── Sentiment ───────────────────────────────────────────────────────
  const nlpSentiment = (nlp.sentiment ?? {}) as Record<string, unknown>;
  const sentimentScore = Number(nlpSentiment.overall_score ?? nlp.optimism_score ?? 50);
  const yoyShift = Number(nlpSentiment.yoy_shift ?? 0);

  type KwRaw = Record<string, unknown>;
  const kwRaw = Array.isArray(nlp.keywords)
    ? (nlp.keywords as KwRaw[])
    : Array.isArray(nlpSentiment.keywords)
    ? (nlpSentiment.keywords as KwRaw[])
    : [];
  const keywords = kwRaw.slice(0, 20).map((k) => ({
    word: String(k.word ?? k.term ?? ""),
    weight: Number(k.weight ?? k.frequency ?? 1),
    tone: (["pos", "neg", "neu"].includes(String(k.tone)) ? k.tone : "neu") as
      | "pos"
      | "neg"
      | "neu",
  }));

  const redFlagsRaw = Array.isArray(risk.red_flags)
    ? (risk.red_flags as string[])
    : Array.isArray(nlp.red_flags)
    ? (nlp.red_flags as string[])
    : [];
  const redFlags = redFlagsRaw.map(String);

  // ── Memo (Engine 5 — not yet connected) ────────────────────────────
  void report;
  const memo = {
    summary: "",
    performance: "",
    bear: Number(valRange.low ?? intrinsicValue * 0.8),
    base: Number(valRange.mid ?? intrinsicValue),
    bull: Number(valRange.high ?? intrinsicValue * 1.2),
    risks: [] as string[],
    thesis: "",
    bearCase: "",
  };

  return {
    ticker,
    name,
    sector,
    industry,
    description: `${name} operates in the ${sector} sector.`,
    price,
    change: 0, // live price change not yet in backend
    marketCap,
    rating,
    intrinsicValue,
    upside,
    wacc,
    terminalGrowth,
    stats,
    peers,
    sensitivity: sensitivityMatrix,
    monteCarlo,
    risk: { level: riskLevel, beta, sharpe, maxDrawdown, var95, altmanZ, debtToEquity, interestCoverage, currentRatio },
    sentiment: { score: sentimentScore, yoyShift, keywords, redFlags },
    memo,
  };
}
