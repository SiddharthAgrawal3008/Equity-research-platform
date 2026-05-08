interface Props {
  data: any;
  onClick: () => void;
  active: boolean;
}

export function NLPCard({ data, onClick, active }: Props) {
  const sentiment = data?.sentiment || {};
  const themes = data?.key_themes || {};
  const coverage = data?.source_coverage || {};
  const redFlags = data?.red_flags || [];

  const scoreColor =
    (sentiment.overall_score ?? 0) > 0.3 ? "text-verdict-under" :
    (sentiment.overall_score ?? 0) > -0.1 ? "text-verdict-fair" :
    "text-verdict-over";

  return (
    <button
      onClick={onClick}
      className={`w-full text-left bg-paper border transition-all ${
        active ? "border-gold shadow-[0_0_0_1px_hsl(var(--gold)/0.3)]" : "border-foreground/10 hover:border-foreground/25"
      } p-5`}
    >
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block h-2 w-2 rounded-full bg-sig-nlp" />
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          NLP Intelligence · Engine 4
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Sentiment</div>
          <div className={`font-serif-display text-2xl mt-0.5 ${scoreColor}`}>
            {sentiment.overall_score != null
              ? (sentiment.overall_score > 0 ? "+" : "") + sentiment.overall_score.toFixed(2)
              : "—"}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">{sentiment.label || ""}</div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Documents</div>
          <div className="font-serif-display text-2xl text-ink mt-0.5">
            {coverage.total_documents ?? "—"}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">analyzed</div>
        </div>
        <div>
          <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Red flags</div>
          <div className={`font-serif-display text-2xl mt-0.5 ${redFlags.length > 0 ? "text-verdict-over" : "text-verdict-under"}`}>
            {redFlags.length}
          </div>
          <div className="font-mono text-[9px] text-muted-foreground">
            {redFlags.length === 0 ? "None found" : "detected"}
          </div>
        </div>
      </div>

      {/* Theme tags */}
      {themes.themes && themes.themes.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {themes.themes.slice(0, 5).map((theme: string, i: number) => (
            <span
              key={i}
              className="px-2 py-1 border border-foreground/10 font-mono text-[9px] uppercase tracking-[0.15em] text-muted-foreground"
            >
              {theme}
            </span>
          ))}
          {themes.themes.length > 5 && (
            <span className="px-2 py-1 font-mono text-[9px] text-muted-foreground">
              +{themes.themes.length - 5} more
            </span>
          )}
        </div>
      )}

      {/* Alignment check */}
      {themes.financial_alignment && (
        <div className={`font-mono text-[10px] ${themes.financial_alignment.aligned ? "text-verdict-under" : "text-verdict-over"}`}>
          {themes.financial_alignment.aligned
            ? "✓ Management language aligns with financials"
            : "⚠ Divergence between management language and financials"}
        </div>
      )}

      <div className="mt-3 font-mono text-[9px] text-gold/70 uppercase tracking-[0.2em]">
        Click for sentiment details, themes & transcript analysis →
      </div>
    </button>
  );
}
