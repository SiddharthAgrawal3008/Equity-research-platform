const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export interface PipelineRequest {
  ticker: string;
  session_id?: string;
  user_id?: string;
}

export async function runPipeline(req: PipelineRequest): Promise<any> {
  const res = await fetch(`${API_URL}/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Chat API ──────────────────────────────────────────────────────────────────

export interface ChatResponse {
  reply: string;
  tool_used: string | null;
  ticker_analyzed: string | null;
  has_analysis: boolean;
}

export async function sendChatMessage(
  message: string,
  history: Array<{ role: string; content: string }>,
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180_000);

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
      signal: controller.signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error("Chat request timed out after 3 min.");
    }
    throw new Error(`Cannot reach backend at ${BASE_URL}.`);
  } finally {
    clearTimeout(timeout);
  }

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Chat failed (${res.status}): ${detail}`);
  }

  return res.json();
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

export async function sendChat(req: ChatRequest): Promise<{ answer: string; model: string }> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  const meta2 = (ctx.metadata ?? {}) as Record<string, unknown>;
  const generatedAt = String(meta2.completed_at ?? meta2.started_at ?? new Date().toISOString());

  return {
    ticker,
    name,
    sector,
    industry,
    description: `${name} operates in the ${sector} sector.`,
    price,
    change: 0,
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
    generatedAt,
  };
}
