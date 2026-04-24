import { CompanyData } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export const RiskTab = ({ c }: { c: CompanyData }) => {
  const r = c.risk;
  const tone =
    r.level === "Low" ? "bull" : r.level === "High" ? "bear" : "neutral";

  const metrics = [
    { l: "Beta (5Y)", v: r.beta.toFixed(2) },
    { l: "Sharpe Ratio", v: r.sharpe.toFixed(2) },
    { l: "Max Drawdown", v: `${r.maxDrawdown.toFixed(1)}%` },
    { l: "Value at Risk (95%)", v: `${r.var95.toFixed(1)}%` },
    { l: "Altman Z-Score", v: r.altmanZ.toFixed(2) },
  ];

  const debt = [
    { l: "Debt / Equity", v: r.debtToEquity, max: 2, fmt: r.debtToEquity.toFixed(2) },
    { l: "Interest Coverage", v: Math.min(r.interestCoverage, 50), max: 50, fmt: `${r.interestCoverage.toFixed(1)}x` },
    { l: "Current Ratio", v: r.currentRatio, max: 3, fmt: r.currentRatio.toFixed(2) },
  ];

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Composite Risk</div>
            <div className="mt-1 font-display text-3xl font-semibold">{r.level}</div>
          </div>
          <Badge
            className={`text-xs ${
              tone === "bull"
                ? "bg-bull text-bull-foreground hover:bg-bull"
                : tone === "bear"
                ? "bg-bear text-bear-foreground hover:bg-bear"
                : "bg-neutral text-neutral-foreground hover:bg-neutral"
            }`}
          >
            {r.level} Risk
          </Badge>
        </div>
      </Card>

      <Card className="border-border bg-card p-6">
        <div className="mb-4 text-sm font-semibold">Risk Metrics</div>
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-border">
              {metrics.map((m) => (
                <tr key={m.l}>
                  <td className="px-4 py-3 text-muted-foreground">{m.l}</td>
                  <td className="px-4 py-3 text-right font-mono-num font-semibold text-foreground">{m.v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="border-border bg-card p-6">
        <div className="mb-5 text-sm font-semibold">Balance Sheet Health</div>
        <div className="space-y-5">
          {debt.map((d) => (
            <div key={d.l}>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{d.l}</span>
                <span className="font-mono-num font-semibold text-foreground">{d.fmt}</span>
              </div>
              <Progress value={(d.v / d.max) * 100} className="h-2" />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
