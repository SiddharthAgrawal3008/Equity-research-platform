import type { CardType } from "@/types/chat";

interface Props {
  type: CardType | null;
  data: any;
  fullContext: any;
  onClose: () => void;
  fullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

function fmtM(val: number | null | undefined): string {
  if (val == null) return "—";
  const abs = Math.abs(val);
  if (abs >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}T`;
  if (abs >= 1_000) return `$${(val / 1_000).toFixed(1)}B`;
  if (abs >= 1) return `$${val.toFixed(1)}M`;
  if (abs > 0) return `${(val * 100).toFixed(1)}%`;
  return "—";
}

function fmtPct(val: number | null | undefined): string {
  if (val == null) return "—";
  return `${(val * 100).toFixed(2)}%`;
}

function fmtNum(val: number | null | undefined, decimals = 2): string {
  if (val == null) return "—";
  return val.toFixed(decimals);
}

export function DetailPanel({ type, data, fullContext, onClose, fullscreen, onToggleFullscreen }: Props) {
  if (!type) return null;

  return (
    <div className="h-full overflow-y-auto">
      <div className="sticky top-0 bg-bone/95 backdrop-blur border-b border-foreground/10 px-6 py-3 flex items-center justify-between z-10">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          {type === "company-header" && "Financial data · Engine 1"}
          {type === "valuation" && "Valuation · Engine 2"}
          {type === "risk" && "Risk & health · Engine 3"}
          {type === "nlp" && "NLP Intelligence · Engine 4"}
          {type === "report" && "Research memo · Engine 5"}
        </span>
        <div className="flex items-center gap-3">
          {onToggleFullscreen && (
            <button onClick={onToggleFullscreen} className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground hover:text-ink transition-colors">
              {fullscreen ? "⊟ Collapse" : "⊞ Expand"}
            </button>
          )}
          <button onClick={onClose} className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground hover:text-ink transition-colors">
            ✕ Close
          </button>
        </div>
      </div>

      <div className={`p-8 ${fullscreen ? "max-w-4xl mx-auto" : ""}`}>
        {type === "company-header" && <FinancialDetail data={data} />}
        {type === "valuation" && <ValuationDetail data={data} />}
        {type === "risk" && <RiskDetail data={data} />}
        {type === "nlp" && <NLPDetail data={data} />}
        {type === "report" && <ReportDetail data={data} />}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-10">
      <h3 className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4 pb-2 border-b border-foreground/10">
        {title}
      </h3>
      {children}
    </div>
  );
}

function KV({ label, value, color }: { label: string; value: any; color?: string }) {
  if (value == null || value === "" || value === "—" || value === "undefined" || value === "null") return null;
  return (
    <div className="flex items-baseline justify-between py-1.5 border-b border-foreground/5">
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
      <span className={`font-mono text-[11px] ${color || "text-ink"}`}>{String(value)}</span>
    </div>
  );
}

function FinancialDetail({ data }: { data: any }) {
  const meta = data?.meta || {};
  const ttm = data?.ttm || {};
  const margins = data?.margins || {};
  const growth = data?.growth || {};
  const returns = data?.returns || {};

  return (
    <>
      <Section title="Company overview">
        <KV label="Company" value={meta.company_name} />
        <KV label="Ticker" value={meta.ticker} />
        <KV label="Sector" value={meta.sector} />
        <KV label="Industry" value={meta.industry} />
        <KV label="Market cap" value={fmtM(meta.market_cap)} />
        <KV label="Current price" value={`$${meta.current_price?.toFixed(2)}`} />
        <KV label="Shares outstanding" value={meta.shares_outstanding?.toLocaleString()} />
      </Section>
      <Section title="Trailing twelve months">
        <KV label="Revenue" value={fmtM(ttm.revenue)} />
        <KV label="EBITDA" value={fmtM(ttm.ebitda)} />
        <KV label="Net income" value={fmtM(ttm.net_income)} />
        <KV label="Operating cash flow" value={fmtM(ttm.operating_cash_flow)} />
        <KV label="Free cash flow" value={fmtM(ttm.free_cash_flow)} />
        <KV label="Effective tax rate" value={ttm.effective_tax_rate != null ? fmtPct(ttm.effective_tax_rate) : null} />
      </Section>
      <Section title="Margins (most recent year)">
        {Object.entries(margins).map(([k, v]) => {
          const arr = v as number[];
          return arr?.[0] != null ? <KV key={k} label={k.replace(/_/g, " ")} value={fmtPct(arr[0])} /> : null;
        })}
      </Section>
      <Section title="Growth (YoY)">
        {Object.entries(growth).map(([k, v]) => {
          const arr = v as number[];
          return arr?.[0] != null ? <KV key={k} label={k.replace(/_/g, " ")} value={fmtPct(arr[0])} /> : null;
        })}
      </Section>
      <Section title="Returns">
        {Object.entries(returns).map(([k, v]) => {
          const arr = v as number[];
          return arr?.[0] != null ? <KV key={k} label={k.replace(/_/g, " ")} value={fmtPct(arr[0])} /> : null;
        })}
      </Section>
    </>
  );
}

function ValuationDetail({ data }: { data: any }) {
  const dcf = data?.dcf || {};
  const rel = data?.relative || {};
  const sens = data?.sensitivity || {};
  const rev = data?.reverse_dcf || {};

  return (
    <>
      <Section title="DCF analysis">
        <KV label="Intrinsic value" value={dcf.intrinsic_value_per_share != null ? `$${dcf.intrinsic_value_per_share.toFixed(2)}` : null} />
        <KV label="Enterprise value" value={dcf.enterprise_value != null ? fmtM(dcf.enterprise_value) : null} />
        <KV label="Equity value" value={dcf.equity_value != null ? fmtM(dcf.equity_value) : null} />
        <KV label="WACC" value={dcf.wacc != null ? fmtPct(dcf.wacc) : null} />
        <KV label="Cost of equity" value={dcf.cost_of_equity != null ? fmtPct(dcf.cost_of_equity) : null} />
        <KV label="Cost of debt" value={dcf.cost_of_debt != null ? fmtPct(dcf.cost_of_debt) : null} />
        <KV label="Beta used" value={dcf.beta_used != null ? fmtNum(dcf.beta_used) : null} />
        <KV label="Risk-free rate" value={dcf.risk_free_rate != null ? fmtPct(dcf.risk_free_rate) : null} />
        <KV label="Equity risk premium" value={dcf.equity_risk_premium != null ? fmtPct(dcf.equity_risk_premium) : null} />
        <KV label="Terminal growth" value={dcf.terminal_growth_rate != null ? fmtPct(dcf.terminal_growth_rate) : null} />
        <KV label="Terminal value %" value={dcf.terminal_value_pct != null ? fmtPct(dcf.terminal_value_pct) : null} />
        <KV label="Projection years" value={dcf.projection_years} />
      </Section>
      <Section title="Relative valuation">
        <KV label="Peers" value={rel.peers?.length ? rel.peers.join(", ") : "Sector averages"} />
        <KV label="PE (company)" value={fmtNum(rel.pe_company)} />
        <KV label="PE (peers median)" value={fmtNum(rel.pe_peers_median)} />
        <KV label="PE implied price" value={rel.pe_implied_value != null ? `$${rel.pe_implied_value.toFixed(2)}` : null} />
        <KV label="PB (company)" value={fmtNum(rel.pb_company)} />
        <KV label="PB (peers median)" value={fmtNum(rel.pb_peers_median)} />
        <KV label="EV/EBITDA (company)" value={fmtNum(rel.ev_ebitda_company)} />
        <KV label="EV/EBITDA implied" value={rel.ev_ebitda_implied_value != null ? `$${rel.ev_ebitda_implied_value.toFixed(2)}` : null} />
      </Section>
      {sens.value_matrix && sens.value_matrix.length > 0 && (
        <Section title="Sensitivity matrix (WACC × growth)">
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-[10px]">
              <thead>
                <tr>
                  <th className="text-left py-1.5 px-2 text-muted-foreground bg-bone/50">WACC ↓ / g →</th>
                  {(sens.growth_range || []).map((g: number, i: number) => (
                    <th key={i} className="text-right py-1.5 px-2 text-muted-foreground bg-bone/50">{(g * 100).toFixed(1)}%</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(sens.value_matrix || []).map((row: number[], ri: number) => (
                  <tr key={ri} className={`border-t border-foreground/5 ${ri % 2 === 0 ? "bg-foreground/[0.02]" : ""}`}>
                    <td className="py-1.5 px-2 text-muted-foreground font-medium">{((sens.wacc_range || [])[ri] * 100).toFixed(1)}%</td>
                    {row.map((val: number, ci: number) => {
                      const isBase = ri === sens.base_case_wacc_idx && ci === sens.base_case_growth_idx;
                      return (
                        <td key={ci} className={`text-right py-1.5 px-2 ${isBase ? "text-gold font-bold bg-gold/10" : "text-ink"}`}>
                          ${val.toFixed(0)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 font-mono text-[9px] text-muted-foreground">Gold highlighted cell = base case assumptions</p>
        </Section>
      )}
      <Section title="Reverse DCF">
        <KV label="Market implied growth" value={rev.implied_growth_rate != null ? fmtPct(rev.implied_growth_rate) : null} />
        <KV label="Forward growth rate" value={rev.forward_growth_rate != null ? fmtPct(rev.forward_growth_rate) : null} />
        <KV label="Market stance" value={rev.market_implied_stance} />
      </Section>
    </>
  );
}

function RiskDetail({ data }: { data: any }) {
  const mr = data?.market_risk || {};
  const fh = data?.financial_health || {};
  const flags = data?.red_flags || [];

  return (
    <>
      <Section title="Market risk">
        <KV label="Beta" value={fmtNum(mr.beta ?? mr.beta_value, 3)} />
        <KV label="Historical volatility" value={mr.volatility_annual != null || mr.historical_volatility != null ? fmtPct(mr.volatility_annual ?? mr.historical_volatility) : null} />
        <KV label="Sharpe ratio" value={fmtNum(mr.sharpe_ratio, 3)} />
        <KV label="Max drawdown" value={mr.max_drawdown != null ? fmtPct(mr.max_drawdown) : null} />
        <KV label="Drawdown period" value={mr.max_drawdown_start ? `${mr.max_drawdown_start} → ${mr.max_drawdown_end}` : null} />
        <KV label="VaR (95% daily)" value={mr.var_95 != null || mr.var_95_daily != null ? fmtPct(mr.var_95 ?? mr.var_95_daily) : null} />
        <KV label="Annualized return" value={mr.annualized_return != null ? fmtPct(mr.annualized_return) : null} />
      </Section>
      <Section title="Financial health">
        <KV label="Altman Z-score" value={fmtNum(fh.altman_z_score, 3)} />
        <KV label="Altman Z zone" value={fh.altman_z_zone} color={fh.altman_z_zone === "Safe" ? "text-verdict-under" : fh.altman_z_zone === "Gray" ? "text-verdict-fair" : "text-verdict-over"} />
        <KV label="Interest coverage" value={fmtNum(fh.interest_coverage)} />
        <KV label="Debt/EBITDA" value={fmtNum(fh.debt_to_ebitda)} />
        <KV label="Current ratio" value={fmtNum(fh.current_ratio)} />
        <KV label="Quick ratio" value={fmtNum(fh.quick_ratio)} />
        <KV label="Debt/Equity" value={fmtNum(fh.debt_to_equity)} />
        <KV label="Cash/Debt" value={fmtNum(fh.cash_to_debt)} />
        <KV label="Earnings quality" value={fmtNum(fh.earnings_quality)} />
      </Section>
      <Section title={`Red flags (${flags.length})`}>
        {flags.length === 0 ? (
          <p className="text-sm text-verdict-under font-mono">No red flags detected ✓</p>
        ) : (
          flags.map((flag: any, i: number) => (
            <div key={i} className="p-3 mb-2 border border-verdict-over/20 bg-verdict-over/5">
              <span className="font-mono text-[10px] text-verdict-over">⚠ {flag.severity || "Warning"}</span>
              <p className="text-sm text-ink mt-1">{flag.flag || flag.message || JSON.stringify(flag)}</p>
              {flag.evidence && <p className="text-xs text-muted-foreground mt-1">{flag.evidence}</p>}
            </div>
          ))
        )}
      </Section>
    </>
  );
}

function NLPDetail({ data }: { data: any }) {
  const sentiment = data?.sentiment || {};
  const themes = data?.key_themes || {};
  const flags = data?.red_flags || [];
  const coverage = data?.source_coverage || {};

  return (
    <>
      <Section title="Sentiment analysis">
        <KV label="Overall score" value={sentiment.overall_score != null ? fmtNum(sentiment.overall_score, 3) : null} />
        <KV label="Label" value={sentiment.label} />
        {sentiment.by_source && Object.entries(sentiment.by_source).map(([src, val]: [string, any]) => (
          <KV key={src} label={src.replace(/_/g, " ")} value={`${val.score?.toFixed(2)} (${val.count} docs)`} />
        ))}
      </Section>
      <Section title="Source coverage">
        <KV label="Earnings transcripts" value={coverage.earnings_transcripts} />
        <KV label="Annual reports" value={coverage.annual_reports} />
        <KV label="Press releases" value={coverage.press_releases} />
        <KV label="Total documents" value={coverage.total_documents} />
      </Section>
      <Section title="Key themes">
        <div className="flex flex-wrap gap-1.5">
          {(themes.themes || []).map((t: string, i: number) => (
            <span key={i} className="px-3 py-1.5 border border-foreground/10 font-mono text-[10px] uppercase tracking-[0.15em] text-ink">{t}</span>
          ))}
          {(!themes.themes || themes.themes.length === 0) && <p className="text-sm text-muted-foreground">No themes extracted</p>}
        </div>
      </Section>
      {themes.financial_alignment && (
        <Section title="Financial alignment">
          <KV label="Aligned" value={themes.financial_alignment.aligned ? "Yes ✓" : "No ⚠"} color={themes.financial_alignment.aligned ? "text-verdict-under" : "text-verdict-over"} />
          {(themes.financial_alignment.divergences || []).map((d: string, i: number) => (
            <div key={i} className="p-2 mb-1 bg-verdict-over/5 border border-verdict-over/15 text-xs text-ink">{d}</div>
          ))}
        </Section>
      )}
      {flags.length > 0 && (
        <Section title="NLP red flags">
          {flags.map((f: any, i: number) => (
            <div key={i} className="p-3 mb-2 border border-verdict-over/20 bg-verdict-over/5">
              <p className="text-sm text-ink font-medium">{f.flag}</p>
              <p className="text-xs text-muted-foreground mt-1">{f.severity} · {f.source}</p>
            </div>
          ))}
        </Section>
      )}
    </>
  );
}

function ReportDetail({ data }: { data: any }) {
  const sections = data?.sections || {};
  const summary = data?.summary || "";

  return (
    <>
      {summary && (
        <Section title="Executive summary">
          <div className="border-l-2 border-gold/60 pl-4">
            <p className="text-base italic text-ink leading-relaxed">{summary}</p>
          </div>
        </Section>
      )}
      {Object.entries(sections).map(([name, text], i) => (
        <Section key={name} title={`${String(i + 1).padStart(2, "0")} · ${name.replace(/_/g, " ")}`}>
          <div className="border-l-2 border-gold/30 pl-4">
            <div className="text-sm text-ink leading-[1.8]">
              {String(text as string).split("\n").map((para, pi) =>
                para.trim() ? <p key={pi} className="mb-4">{para}</p> : null
              )}
            </div>
          </div>
        </Section>
      ))}
      {Object.keys(sections).length === 0 && (
        <p className="text-sm text-muted-foreground">No report sections available.</p>
      )}
    </>
  );
}
