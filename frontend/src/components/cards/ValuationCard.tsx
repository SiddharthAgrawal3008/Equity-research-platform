interface Props {
  data: any;
  onClick: () => void;
  active: boolean;
}

export function ValuationCard({ data, onClick, active }: Props) {
  const dcf = data?.dcf || {};
  const relative = data?.relative || {};
  const summary = data?.summary || {};
  const range = data?.valuation_range || {};

  const verdictColor = {
    Undervalued: "text-verdict-under",
    "Fairly Valued": "text-verdict-fair",
    Overvalued: "text-verdict-over",
  }[summary.verdict as string] || "text-muted-foreground";

  const confidenceColor = {
    High: "text-verdict-under",
    Medium: "text-gold",
    Low: "text-verdict-over",
    Unreliable: "text-verdict-over",
  }[summary.confidence as string] || "text-muted-foreground";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-paper border transition-all ${
        active ? "border-gold shadow-[0_0_0_1px_hsl(var(--gold)/0.3)]" : "border-foreground/10 hover:border-foreground/25"
      } p-5`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block h-2 w-2 rounded-full bg-sig-valuation" />
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          Valuation · Engine 2
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">DCF Value</div>
          <div className="font-serif-display text-2xl text-ink mt-0.5">
            {dcf.intrinsic_value_per_share != null
              ? `$${dcf.intrinsic_value_per_share.toFixed(2)}`
              : "—"}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Verdict</div>
          <div className={`font-serif-display text-2xl mt-0.5 ${verdictColor}`}>
            {summary.verdict || "—"}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Confidence</div>
          <div className={`font-serif-display text-2xl mt-0.5 ${confidenceColor}`}>
            {summary.confidence || "—"}
          </div>
        </div>
      </div>

      {/* Valuation range bar */}
      {range.low != null && range.high != null && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="font-mono text-[9px] text-muted-foreground">${range.low?.toFixed(0)}</span>
            <span className="font-mono text-[9px] text-muted-foreground">Valuation range</span>
            <span className="font-mono text-[9px] text-muted-foreground">${range.high?.toFixed(0)}</span>
          </div>
          <div className="relative h-2 bg-bone rounded-full overflow-hidden">
            <div className="absolute inset-y-0 left-[15%] right-[15%] bg-gold/40 rounded-full" />
            {summary.current_price && range.low && range.high && (
              <div
                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-4 w-4 rounded-full bg-ink border-2 border-paper"
                style={{
                  left: `${Math.max(5, Math.min(95, ((summary.current_price - range.low) / (range.high - range.low)) * 100))}%`,
                }}
              />
            )}
          </div>
        </div>
      )}

      {summary.upside_pct != null && (
        <div className="font-mono text-[10px] text-muted-foreground">
          Upside: <span className={summary.upside_pct > 0 ? "text-verdict-under" : "text-verdict-over"}>
            {summary.upside_pct > 0 ? "+" : ""}{(summary.upside_pct * 100).toFixed(1)}%
          </span>
        </div>
      )}

      <div className="mt-3 font-mono text-[9px] text-gold/70 uppercase tracking-[0.2em]">
        Click for DCF breakdown, sensitivity & relative valuation →
      </div>
    </button>
  );
}
