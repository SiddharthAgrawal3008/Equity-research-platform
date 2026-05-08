import { useEffect, useState } from "react";

const ENGINES = [
  { id: 1, name: "Financial Data", color: "bg-sig-data", duration: 8.2, stage: 1 },
  { id: 2, name: "Valuation", color: "bg-sig-valuation", duration: 12.1, stage: 2 },
  { id: 3, name: "Risk", color: "bg-sig-risk", duration: 6.4, stage: 2 },
  { id: 4, name: "NLP Intelligence", color: "bg-sig-nlp", duration: 11.8, stage: 2 },
  { id: 5, name: "Report", color: "bg-sig-report", duration: 3.5, stage: 3 },
];

export function PipelineLoader() {
  const [progress, setProgress] = useState<number[]>([0, 0, 0, 0, 0]);

  useEffect(() => {
    const start = Date.now();
    const totals = ENGINES.map((e) => e.duration);

    const id = setInterval(() => {
      const t = (Date.now() - start) / 1000;
      const p = totals.map((dur, i) => {
        const s = i === 0 ? 0 : i === 4 ? 1 + Math.max(totals[1], totals[2], totals[3]) : totals[0];
        const local = (t - s) / dur;
        return Math.max(0, Math.min(1, local));
      });
      setProgress(p);
    }, 80);

    return () => clearInterval(id);
  }, []);

  const completed = progress.filter((p) => p >= 1).length;
  const elapsed = progress.reduce((acc, p, i) => Math.max(acc, p * ENGINES[i].duration), 0);

  return (
    <div className="bg-terminal text-terminal-foreground p-5 border border-terminal-line">
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim mb-4">
        <span className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-gold pulse-dot" />
          Pipeline running
        </span>
        <span>{completed}/5 engines · {elapsed.toFixed(1)}s</span>
      </div>

      <div className="space-y-2.5">
        {ENGINES.map((e, i) => {
          const pct = progress[i];
          const done = pct >= 1;
          const active = pct > 0 && pct < 1;
          return (
            <div key={e.id}>
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.18em] mb-1">
                <span className="flex items-center gap-2">
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${e.color} ${active ? "pulse-dot" : ""}`} />
                  <span className="text-terminal-dim">E{e.id}</span>
                  <span className="text-terminal-foreground">{e.name}</span>
                  {e.stage === 2 && <span className="text-terminal-dim/50">parallel</span>}
                </span>
                <span className="text-terminal-dim">
                  {done ? "✓" : active ? `${(pct * 100).toFixed(0)}%` : "—"}
                </span>
              </div>
              <div className="h-[3px] bg-terminal-line/60 overflow-hidden">
                <div
                  className={`h-full ${e.color} transition-[width] duration-100`}
                  style={{ width: `${pct * 100}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
