import { CompanyData } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const OverviewTab = ({ c }: { c: CompanyData }) => (
  <div className="space-y-6">
    <Card className="border-border bg-card p-6">
      <div className="mb-3 flex items-center gap-2">
        <Badge variant="outline" className="border-border">{c.sector}</Badge>
        <Badge variant="outline" className="border-border">{c.industry}</Badge>
      </div>
      <h3 className="font-display text-lg font-semibold">About {c.name}</h3>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{c.description}</p>
    </Card>

    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[
        { l: "Revenue (TTM)", v: c.stats.revenue },
        { l: "EPS (TTM)", v: c.stats.eps },
        { l: "P/E", v: c.stats.pe },
        { l: "EV / EBITDA", v: c.stats.evEbitda },
      ].map((s) => (
        <Card key={s.l} className="border-border bg-card p-5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{s.l}</div>
          <div className="mt-2 font-mono-num text-2xl font-semibold text-foreground">{s.v}</div>
        </Card>
      ))}
    </div>

    <Card className="border-border bg-card p-6">
      <div className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quick read</div>
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { l: "Intrinsic value", v: `$${c.intrinsicValue.toFixed(2)}` },
          { l: "Implied upside", v: `${c.upside > 0 ? "+" : ""}${c.upside.toFixed(1)}%`, t: c.upside >= 0 ? "bull" : "bear" },
          { l: "Risk level", v: c.risk.level, t: c.risk.level === "Low" ? "bull" : c.risk.level === "High" ? "bear" : "neutral" },
        ].map((m) => (
          <div key={m.l}>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{m.l}</div>
            <div
              className={`mt-1 font-mono-num text-xl font-semibold ${
                m.t === "bull" ? "text-bull" : m.t === "bear" ? "text-bear" : m.t === "neutral" ? "text-neutral" : "text-foreground"
              }`}
            >
              {m.v}
            </div>
          </div>
        ))}
      </div>
    </Card>
  </div>
);
