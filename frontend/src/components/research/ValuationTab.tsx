import { CompanyData } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";

export const ValuationTab = ({ c }: { c: CompanyData }) => {
  const growthLabels = ["1.5%", "2.0%", "2.5%", "3.0%", "3.5%"];
  const waccLabels = ["7.5%", "8.0%", "8.5%", "9.0%", "9.5%"];
  const all = c.sensitivity.flat();
  const min = Math.min(...all);
  const max = Math.max(...all);

  return (
    <div className="space-y-6">
      {/* DCF headline */}
      <Card className="border-border bg-card p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">DCF Intrinsic Value</div>
            <div className="mt-1 font-mono-num text-4xl font-semibold text-foreground">${c.intrinsicValue.toFixed(2)}</div>
            <div className="mt-1 text-xs text-muted-foreground">vs. current ${c.price.toFixed(2)}</div>
          </div>
          <div className="text-right">
            <Badge className={c.upside >= 0 ? "bg-bull text-bull-foreground hover:bg-bull" : "bg-bear text-bear-foreground hover:bg-bear"}>
              {c.upside >= 0 ? "+" : ""}{c.upside.toFixed(1)}% {c.upside >= 0 ? "upside" : "downside"}
            </Badge>
            <div className="mt-2 font-mono-num text-xs text-muted-foreground">WACC {c.wacc}% · g {c.terminalGrowth}%</div>
          </div>
        </div>
      </Card>

      {/* Relative valuation */}
      <Card className="border-border bg-card p-6">
        <div className="mb-4 text-sm font-semibold">Relative Valuation</div>
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 text-left">Ticker</th>
                <th className="px-4 py-2.5 text-right">P/E</th>
                <th className="px-4 py-2.5 text-right">EV/EBITDA</th>
                <th className="px-4 py-2.5 text-right">P/B</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono-num">
              {c.peers.map((p) => (
                <tr key={p.ticker} className={p.ticker === c.ticker ? "bg-accent-soft/40" : ""}>
                  <td className="px-4 py-2.5 font-semibold text-foreground">{p.ticker}</td>
                  <td className="px-4 py-2.5 text-right">{p.pe.toFixed(1)}x</td>
                  <td className="px-4 py-2.5 text-right">{p.ev.toFixed(1)}x</td>
                  <td className="px-4 py-2.5 text-right">{p.pb.toFixed(1)}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Sensitivity heatmap */}
      <Card className="border-border bg-card p-6">
        <div className="mb-1 text-sm font-semibold">Sensitivity Analysis</div>
        <div className="mb-4 text-xs text-muted-foreground">Intrinsic value ($) — Terminal growth (rows) × WACC (cols)</div>
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full">
            <div className="grid grid-cols-[64px_repeat(5,1fr)] gap-1 text-xs">
              <div />
              {waccLabels.map((w) => (
                <div key={w} className="px-2 py-1.5 text-center font-mono-num text-muted-foreground">{w}</div>
              ))}
              {c.sensitivity.map((row, r) => (
                <>
                  <div key={`l${r}`} className="flex items-center justify-end pr-2 font-mono-num text-muted-foreground">
                    {growthLabels[r]}
                  </div>
                  {row.map((v, ci) => {
                    const t = (v - min) / (max - min || 1);
                    const isBase = r === 2 && ci === 2;
                    return (
                      <div
                        key={`${r}-${ci}`}
                        className={`flex h-12 items-center justify-center rounded font-mono-num text-xs font-semibold ${
                          isBase ? "ring-2 ring-accent" : ""
                        }`}
                        style={{
                          background: `hsl(var(--accent) / ${(0.1 + t * 0.7).toFixed(2)})`,
                          color: t > 0.5 ? "hsl(var(--accent-foreground))" : "hsl(var(--foreground))",
                        }}
                      >
                        ${v.toFixed(0)}
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Monte Carlo distribution */}
      <Card className="border-border bg-card p-6">
        <div className="mb-1 text-sm font-semibold">Monte Carlo Distribution</div>
        <div className="mb-4 text-xs text-muted-foreground">10,000 simulated outcomes — base case ${c.intrinsicValue.toFixed(0)}</div>
        <div className="h-64">
          <ResponsiveContainer>
            <AreaChart data={c.monteCarlo} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="mcGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="v" stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 11 }} />
              <YAxis stroke="hsl(var(--muted-foreground))" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v: number) => [`${v}%`, "Probability"]}
                labelFormatter={(l) => `$${l}`}
              />
              <ReferenceLine x={c.intrinsicValue} stroke="hsl(var(--accent))" strokeDasharray="4 4" label={{ value: "Base", fill: "hsl(var(--accent))", fontSize: 10 }} />
              <Area type="monotone" dataKey="freq" stroke="hsl(var(--accent))" strokeWidth={2} fill="url(#mcGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};
