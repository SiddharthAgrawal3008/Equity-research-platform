interface Props {
  data: any;
  onClick: () => void;
  active: boolean;
}

function formatCurrency(val: number | null | undefined, unit: "M" | "raw" = "M"): string {
  if (val == null || val === 0) return "—";
  const abs = Math.abs(val);
  if (unit === "M") {
    if (abs >= 1e6) return `$${(val / 1e6).toFixed(2)}T`;
    if (abs >= 1e3) return `$${(val / 1e3).toFixed(1)}B`;
    return `$${val.toFixed(1)}M`;
  }
  if (abs >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
  return `$${val.toLocaleString()}`;
}

export function CompanyHeaderCard({ data, onClick, active }: Props) {
  const meta = data?.meta || {};
  const ttm = data?.ttm || {};

  const mktCap = meta.market_cap;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-paper border transition-all ${
        active ? "border-gold shadow-[0_0_0_1px_hsl(var(--gold)/0.3)]" : "border-foreground/10 hover:border-foreground/25"
      } p-5`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-block h-2 w-2 rounded-full bg-sig-data" />
            <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
              Financial data · Engine 1
            </span>
          </div>
          <h3 className="font-serif-display text-2xl text-ink leading-tight">
            {meta.company_name || meta.ticker || "—"}
          </h3>
          <div className="flex items-center gap-3 mt-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            <span>{meta.ticker}</span>
            <span>·</span>
            <span>{meta.sector}</span>
            <span>·</span>
            <span>{meta.currency || "USD"}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="font-serif-display text-3xl text-ink">
            ${meta.current_price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "—"}
          </div>
          <div className="font-mono text-[10px] text-muted-foreground mt-1">
            Mkt cap: {formatCurrency(mktCap, "M")}
          </div>
        </div>
      </div>

      {(ttm.revenue || ttm.net_income || ttm.free_cash_flow) && (
        <div className="grid grid-cols-4 gap-3 mt-5 pt-4 border-t border-foreground/8">
          <MiniStat label="Revenue TTM" value={formatCurrency(ttm.revenue, "M")} />
          <MiniStat label="Net Income" value={formatCurrency(ttm.net_income, "M")} />
          <MiniStat label="FCF" value={formatCurrency(ttm.free_cash_flow, "M")} />
          <MiniStat label="EBITDA" value={formatCurrency(ttm.ebitda, "M")} />
        </div>
      )}

      <div className="mt-3 font-mono text-[9px] text-gold/70 uppercase tracking-[0.2em]">
        Click to view full financials →
      </div>
    </button>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">{label}</div>
      <div className="font-serif-display text-lg text-ink mt-0.5">{value}</div>
    </div>
  );
}
