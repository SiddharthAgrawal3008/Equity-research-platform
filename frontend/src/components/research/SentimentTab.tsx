import { CompanyData } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react";

export const SentimentTab = ({ c }: { c: CompanyData }) => {
  const s = c.sentiment;
  const angle = (s.score / 100) * 180;

  return (
    <div className="space-y-6">
      <Card className="border-border bg-card p-6">
        <div className="grid gap-6 sm:grid-cols-[260px_1fr] sm:items-center">
          <div className="flex flex-col items-center">
            <Gauge value={s.score} angle={angle} />
            <div className="mt-2 text-[11px] uppercase tracking-wider text-muted-foreground">Management sentiment</div>
          </div>
          <div className="space-y-4">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Year-over-year shift</div>
              <div
                className={`mt-1 inline-flex items-center gap-1.5 font-mono-num text-2xl font-semibold ${
                  s.yoyShift >= 0 ? "text-bull" : "text-bear"
                }`}
              >
                {s.yoyShift >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                {s.yoyShift >= 0 ? "+" : ""}{s.yoyShift.toFixed(1)} pts
              </div>
              <p className="mt-1 text-xs text-muted-foreground">vs. last fiscal year management commentary.</p>
            </div>
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Overall tone</div>
              <p className="text-sm text-foreground/80">
                Sourced from latest 10-K, Q-filings and earnings call transcripts —
                weighted by speaker (CEO/CFO) and topic salience.
              </p>
            </div>
          </div>
        </div>
      </Card>

      <Card className="border-border bg-card p-6">
        <div className="mb-4 text-sm font-semibold">Top extracted keywords</div>
        <div className="flex flex-wrap gap-2">
          {s.keywords.map((k) => (
            <span
              key={k.word}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium ${
                k.tone === "pos"
                  ? "border-bull/30 bg-bull/10 text-bull"
                  : k.tone === "neg"
                  ? "border-bear/30 bg-bear/10 text-bear"
                  : "border-border bg-surface-muted text-muted-foreground"
              }`}
              style={{ fontSize: `${0.72 + (k.weight / 100) * 0.4}rem` }}
            >
              {k.word}
              <span className="font-mono-num opacity-70">· {k.weight}</span>
            </span>
          ))}
        </div>
      </Card>

      {s.redFlags.length > 0 && (
        <Card className="border-bear/30 bg-bear/5 p-6">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-bear">
            <AlertTriangle className="h-4 w-4" /> Red flags detected
          </div>
          <ul className="space-y-2 text-sm">
            {s.redFlags.map((f) => (
              <li key={f} className="flex items-start gap-2">
                <Badge className="mt-0.5 bg-bear text-bear-foreground hover:bg-bear">!</Badge>
                <span className="text-foreground/90">{f}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};

const Gauge = ({ value, angle }: { value: number; angle: number }) => {
  const radius = 80;
  const cx = 100;
  const cy = 100;

  const polar = (a: number) => {
    const rad = ((180 - a) * Math.PI) / 180;
    return [cx + radius * Math.cos(rad), cy - radius * Math.sin(rad)];
  };
  const arc = (start: number, end: number, color: string) => {
    const [x1, y1] = polar(start);
    const [x2, y2] = polar(end);
    const large = end - start > 180 ? 1 : 0;
    return <path d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2}`} stroke={color} strokeWidth="14" fill="none" strokeLinecap="round" />;
  };
  const [nx, ny] = polar(angle);

  return (
    <svg viewBox="0 0 200 120" className="h-32 w-48">
      {arc(0, 60, "hsl(var(--bear))")}
      {arc(60, 120, "hsl(var(--neutral))")}
      {arc(120, 180, "hsl(var(--bull))")}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="hsl(var(--foreground))" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="6" fill="hsl(var(--foreground))" />
      <text x={cx} y={cy + 28} textAnchor="middle" className="fill-foreground font-mono-num text-2xl font-semibold">
        {value}
      </text>
    </svg>
  );
};
