interface Props {
  data: any;
  onClick: () => void;
  active: boolean;
}

export function RiskCard({ data, onClick, active }: Props) {
  const mr = data?.market_risk || {};
  const fh = data?.financial_health || {};

  const zZone = fh.altman_z_zone || fh.altman_z_zone;
  const zColor = zZone === "Safe" ? "text-verdict-under" : zZone === "Gray" ? "text-verdict-fair" : "text-verdict-over";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-paper border transition-all ${
        active ? "border-gold shadow-[0_0_0_1px_hsl(var(--gold)/0.3)]" : "border-foreground/10 hover:border-foreground/25"
      } p-5`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block h-2 w-2 rounded-full bg-sig-risk" />
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          Risk & Financial Health · Engine 3
        </span>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Altman Z</div>
          <div className={`font-serif-display text-xl mt-0.5 ${zColor}`}>
            {fh.altman_z_score?.toFixed(2) ?? "—"}
          </div>
          <div className={`font-mono text-[9px] ${zColor}`}>{zZone || ""}</div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Beta</div>
          <div className="font-serif-display text-xl text-ink mt-0.5">
            {(mr.beta ?? mr.beta_value)?.toFixed(2) ?? "—"}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">vs S&P 500</div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Sharpe</div>
          <div className="font-serif-display text-xl text-ink mt-0.5">
            {mr.sharpe_ratio?.toFixed(2) ?? "—"}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">Risk-adj</div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Max DD</div>
          <div className="font-serif-display text-xl text-verdict-over mt-0.5">
            {mr.max_drawdown != null ? `${(mr.max_drawdown * 100).toFixed(0)}%` : "—"}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">
            {mr.max_drawdown_start?.slice(0, 4) || ""}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-foreground/8">
        <MiniHealth label="Interest Cov" value={fh.interest_coverage?.toFixed(1)} />
        <MiniHealth label="Debt/EBITDA" value={fh.debt_to_ebitda?.toFixed(2)} />
        <MiniHealth label="Current Ratio" value={fh.current_ratio?.toFixed(2)} />
      </div>

      <div className="mt-3 font-mono text-[9px] text-gold/70 uppercase tracking-[0.2em]">
        Click for full risk profile, VaR, red flags & health metrics →
      </div>
    </button>
  );
}

function MiniHealth({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">{label}</div>
      <div className="font-serif-display text-base text-ink mt-0.5">{value ?? "—"}</div>
    </div>
  );
}
