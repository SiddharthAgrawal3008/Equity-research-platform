import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform, useInView } from "framer-motion";
import { Link } from "react-router-dom";

// ─────────────────────────────────────────────────────────────
// EQUIMIND — Editorial Terminal
// One ticker. Five engines. One memo.
// ─────────────────────────────────────────────────────────────

const ENGINES = [
  { id: 1, name: "Financial Data",   author: "Divyansh", stage: 1, color: "sig-data",       desc: "Standardize · derive · TTM · validate", duration: 8.2,  reads: ["ticker"], writes: "financial_data" },
  { id: 2, name: "Valuation",        author: "Siddharth", stage: 2, color: "sig-valuation", desc: "DCF · relative · sensitivity · reverse",  duration: 12.1, reads: ["financial_data"], writes: "valuation" },
  { id: 3, name: "Risk",             author: "Siddharth", stage: 2, color: "sig-risk",      desc: "Beta · VaR · Sharpe · Altman Z · flags",  duration: 6.4,  reads: ["financial_data"], writes: "risk_metrics" },
  { id: 4, name: "NLP Intelligence", author: "Annant",    stage: 2, color: "sig-nlp",       desc: "Earnings calls · 10-K · sentiment",       duration: 11.8, reads: ["financial_data"], writes: "nlp_insights" },
  { id: 5, name: "Report",           author: "Naman",     stage: 3, color: "sig-report",    desc: "6 narratives · base · bear · PDF",        duration: 3.5,  reads: ["all"], writes: "report" },
] as const;

const TICKERS = ["AAPL","MSFT","NVDA","TSLA","GOOGL","META","AMZN","JPM","BRK.B","V","UNH","XOM","WMT","LLY","AVGO","COST","HD","NFLX","ORCL","AMD"];

// ──────────────── HERO ────────────────
function Hero() {
  const [ticker, setTicker] = useState("AAPL");
  const [phase, setPhase] = useState<"idle" | "running">("idle");

  const run = () => {
    if (phase === "running") return;
    setPhase("running");
    setTimeout(() => setPhase("idle"), 6000);
  };

  return (
    <section className="relative overflow-hidden bg-paper border-b border-foreground/10">
      {/* corner marks */}
      <CornerMarks />

      <div className="container max-w-7xl pt-10 pb-16">
        {/* top meta bar */}
        <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground mb-16">
          <div className="flex items-center gap-3">
            <span className="inline-block h-2 w-2 rounded-full bg-verdict-under pulse-dot" />
            <span>System nominal · 5/5 engines online</span>
          </div>
          <div className="hidden md:flex items-center gap-6">
            <span>Vol. I · No. 03</span>
            <span>MMXXVI</span>
            <span>EQUIMIND.APP</span>
          </div>
        </div>

        <div className="grid md:grid-cols-12 gap-8 items-end">
          {/* Left: massive editorial headline */}
          <div className="md:col-span-8">
            <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-gold mb-6">
              ¶ The Equimind Method — Issue 003
            </div>
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
              className="font-serif-display text-[14vw] md:text-[8.2rem] leading-[0.86] tracking-[-0.04em] text-ink"
            >
              What is
              <br />
              <span className="italic font-light">a company</span>
              <br />
              <span className="relative">
                <span className="text-gold">actually</span>
                <span className="text-ink"> worth?</span>
              </span>
            </motion.h1>

            <p className="mt-10 max-w-xl text-base text-foreground/70 leading-relaxed">
              Five autonomous engines read the filings, run the valuation, score the risk,
              parse the earnings call and write the memo. Type a ticker.
              <span className="font-serif-display italic text-ink"> The verdict arrives in thirty seconds.</span>
            </p>
          </div>

          {/* Right: vertical metadata column */}
          <div className="md:col-span-4 md:pl-8 md:border-l border-foreground/15">
            <div className="space-y-6 font-mono text-[11px] uppercase tracking-[0.18em]">
              <MetaRow k="Engines" v="05 · parallel" />
              <MetaRow k="Sources" v="AV · Finnhub · EDGAR · FMP" />
              <MetaRow k="Output" v="6-section memo · PDF" />
              <MetaRow k="Latency" v="≈ 27.4 s p50" />
              <MetaRow k="Coverage" v="US equities" />
              <MetaRow k="Architecture" v="Orchestrator + Data Bus" />
            </div>
          </div>
        </div>

        {/* The Terminal Input — the centerpiece */}
        <div className="mt-20">
          <TerminalInput ticker={ticker} setTicker={setTicker} onRun={run} phase={phase} />
        </div>
      </div>
    </section>
  );
}

function MetaRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-foreground/10 pb-2">
      <span className="text-muted-foreground">{k}</span>
      <span className="text-ink">{v}</span>
    </div>
  );
}

function CornerMarks() {
  const M = ({ className }: { className: string }) => (
    <div className={`absolute h-4 w-4 ${className}`}>
      <div className="absolute inset-0 border-ink/40" />
    </div>
  );
  return (
    <>
      <div className="absolute top-4 left-4 h-3 w-3 border-l border-t border-ink/40" />
      <div className="absolute top-4 right-4 h-3 w-3 border-r border-t border-ink/40" />
      <div className="absolute bottom-4 left-4 h-3 w-3 border-l border-b border-ink/40" />
      <div className="absolute bottom-4 right-4 h-3 w-3 border-r border-b border-ink/40" />
    </>
  );
}

// ──────────────── TERMINAL INPUT ────────────────
function TerminalInput({ ticker, setTicker, onRun, phase }: any) {
  const [time, setTime] = useState("");
  useEffect(() => {
    const t = () => setTime(new Date().toUTCString().slice(17, 25));
    t();
    const i = setInterval(t, 1000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="relative bg-terminal text-terminal-foreground rounded-sm overflow-hidden shadow-[0_40px_80px_-20px_hsl(var(--ink)/0.35)]">
      {/* top window bar */}
      <div className="flex items-center justify-between px-5 py-2.5 border-b border-terminal-line bg-black/40">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">
          <span className="h-2 w-2 rounded-full bg-verdict-over/80" />
          <span className="h-2 w-2 rounded-full bg-gold/80" />
          <span className="h-2 w-2 rounded-full bg-verdict-under/80" />
          <span className="ml-3">equimind ── orchestrator ── tty/0</span>
        </div>
        <div className="font-mono text-[10px] text-terminal-dim tracking-widest">{time} UTC</div>
      </div>

      <div className="grid md:grid-cols-12 gap-0">
        {/* Input panel */}
        <div className="md:col-span-7 p-10 md:p-14 relative">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold/80 mb-6">
            $ analyze --ticker
          </div>
          <div className="flex items-baseline gap-5">
            <span className="font-serif-display text-5xl md:text-7xl text-gold/80 leading-none">$</span>
            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase().slice(0, 6))}
              onKeyDown={(e) => e.key === "Enter" && onRun()}
              className="bg-transparent outline-none border-0 font-serif-display text-6xl md:text-8xl tracking-[-0.03em] text-terminal-foreground w-full placeholder:text-terminal-dim/40"
              placeholder="AAPL"
            />
            <span className="font-serif-display text-6xl md:text-8xl text-gold blink leading-none">_</span>
          </div>

          <div className="mt-8 h-px w-full bg-terminal-line" />

          <div className="mt-6 flex flex-wrap items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-terminal-dim">
            <span>Suggest:</span>
            {TICKERS.slice(0, 8).map((t) => (
              <button
                key={t}
                onClick={() => setTicker(t)}
                className="px-2 py-1 border border-terminal-line hover:border-gold hover:text-gold transition-colors"
              >
                {t}
              </button>
            ))}
          </div>

          <button
            onClick={onRun}
            disabled={phase === "running"}
            className="group mt-10 inline-flex items-center gap-4 font-mono text-xs uppercase tracking-[0.3em]"
          >
            <span className="relative flex items-center justify-center h-14 w-14 rounded-full bg-gold text-ink transition-transform group-hover:scale-110">
              {phase === "running" ? (
                <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" opacity="0.3" />
                  <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2" />
                </svg>
              ) : (
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              )}
            </span>
            <span className="text-terminal-foreground group-hover:text-gold transition-colors">
              {phase === "running" ? "Pipeline running…" : "Generate research memo"}
            </span>
          </button>
        </div>

        {/* Live pipeline panel */}
        <div className="md:col-span-5 border-t md:border-t-0 md:border-l border-terminal-line bg-black/30">
          <LivePipeline phase={phase} />
        </div>
      </div>

      {/* bottom status strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-2.5 border-t border-terminal-line bg-black/50 font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">
        <div className="flex items-center gap-4">
          <span><span className="text-gold">●</span> orchestrator</span>
          <span><span className="text-verdict-under">●</span> data bus ready</span>
          <span className="hidden md:inline">5 engines · 3 stages · DAG resolved</span>
        </div>
        <span>↵ enter to run · ⌘K cmd</span>
      </div>
    </div>
  );
}

// ──────────────── LIVE PIPELINE (animated) ────────────────
function LivePipeline({ phase }: { phase: "idle" | "running" }) {
  const [progress, setProgress] = useState<number[]>([0, 0, 0, 0, 0]);

  useEffect(() => {
    if (phase !== "running") {
      setProgress([0, 0, 0, 0, 0]);
      return;
    }
    const start = Date.now();
    const totals = ENGINES.map((e) => e.duration);
    const stageStart = [0, 1, 1, 1, totals[1] + totals.slice(2, 4).reduce((a, b) => Math.max(a, b), 0) / totals[1] + 1];
    const id = setInterval(() => {
      const t = (Date.now() - start) / 1000;
      const p = totals.map((dur, i) => {
        const s = i === 0 ? 0 : i === 4 ? 1 + Math.max(totals[1], totals[2], totals[3]) : 1;
        const local = (t - s) / dur;
        return Math.max(0, Math.min(1, local));
      });
      setProgress(p);
      if (t > 30) clearInterval(id);
    }, 80);
    return () => clearInterval(id);
  }, [phase]);

  return (
    <div className="p-6 md:p-8">
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim mb-5">
        <span>● live pipeline</span>
        <span>{phase === "running" ? "executing" : "standby"}</span>
      </div>

      <div className="space-y-3">
        {ENGINES.map((e, i) => {
          const pct = progress[i];
          const active = phase === "running" && pct > 0 && pct < 1;
          const done = pct >= 1;
          return (
            <div key={e.id} className="space-y-1">
              <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.18em]">
                <span className="flex items-center gap-2">
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full ${active ? "pulse-dot" : ""}`}
                    style={{ background: `hsl(var(--${e.color}))` }}
                  />
                  <span className="text-terminal-dim">E{e.id}</span>
                  <span className="text-terminal-foreground">{e.name}</span>
                </span>
                <span className="text-terminal-dim">
                  {done ? "✓" : active ? `${(pct * e.duration).toFixed(1)}s` : `${e.duration}s`}
                </span>
              </div>
              <div className="h-[3px] bg-terminal-line/60 relative overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 transition-[width] duration-100"
                  style={{ width: `${pct * 100}%`, background: `hsl(var(--${e.color}))` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-terminal-line flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">
        <span>Stages</span>
        <span className="flex items-center gap-1.5">
          <Stage n={1} active={phase === "running" && progress[0] < 1} done={progress[0] >= 1} />
          <ArrowSm />
          <Stage n={2} active={phase === "running" && progress[1] > 0 && (progress[1] < 1 || progress[2] < 1 || progress[3] < 1)} done={progress[1] >= 1 && progress[2] >= 1 && progress[3] >= 1} />
          <ArrowSm />
          <Stage n={3} active={phase === "running" && progress[4] > 0 && progress[4] < 1} done={progress[4] >= 1} />
        </span>
      </div>
    </div>
  );
}

const ArrowSm = () => <span className="text-terminal-dim">→</span>;
function Stage({ n, active, done }: { n: number; active: boolean; done: boolean }) {
  return (
    <span
      className={`inline-flex h-5 w-5 items-center justify-center rounded-full border text-[9px] ${
        done ? "bg-gold border-gold text-ink" : active ? "border-gold text-gold" : "border-terminal-line text-terminal-dim"
      }`}
    >
      {n}
    </span>
  );
}

// ──────────────── MARQUEE ────────────────
function TickerMarquee() {
  const data = TICKERS.map((t, i) => ({
    t,
    p: (Math.sin(i * 1.7) * 4 + (i % 3 === 0 ? -1 : 2)).toFixed(2),
  }));
  return (
    <div className="bg-terminal text-terminal-foreground border-y border-terminal-line overflow-hidden">
      <div className="flex marquee whitespace-nowrap py-3 font-mono text-[11px] tracking-[0.15em]">
        {[...data, ...data].map((d, i) => (
          <span key={i} className="px-6 flex items-center gap-3">
            <span className="text-terminal-dim">{d.t}</span>
            <span className={Number(d.p) >= 0 ? "text-verdict-under" : "text-verdict-over"}>
              {Number(d.p) >= 0 ? "▲" : "▼"} {Math.abs(Number(d.p)).toFixed(2)}%
            </span>
            <span className="text-terminal-dim/40">·</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ──────────────── ENGINES SECTION ────────────────
function EnginesSection() {
  return (
    <section className="bg-terminal text-terminal-foreground py-28 relative overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-[0.06]" />
      <div className="container max-w-7xl relative">
        <SectionHeader
          eyebrow="§ ii · the engines"
          title={<>Five engines.<br /><span className="italic font-light text-gold">One conviction.</span></>}
          desc="A central orchestrator dispatches work across a typed data bus. Stage 1 fetches; Stage 2 thinks in parallel; Stage 3 writes."
          dark
        />

        {/* Stage diagram */}
        <div className="mt-20 grid md:grid-cols-12 gap-6">
          {/* Stage 1 */}
          <div className="md:col-span-3">
            <StageLabel n={1} label="Ingest" />
            <EngineCard e={ENGINES[0]} />
          </div>

          {/* connector */}
          <div className="hidden md:flex md:col-span-1 items-center justify-center">
            <Connector />
          </div>

          {/* Stage 2 */}
          <div className="md:col-span-5">
            <StageLabel n={2} label="Parallel analysis" />
            <div className="grid grid-cols-1 gap-4">
              <EngineCard e={ENGINES[1]} />
              <EngineCard e={ENGINES[2]} />
              <EngineCard e={ENGINES[3]} />
            </div>
          </div>

          <div className="hidden md:flex md:col-span-1 items-center justify-center">
            <Connector />
          </div>

          {/* Stage 3 */}
          <div className="md:col-span-2">
            <StageLabel n={3} label="Synthesize" />
            <EngineCard e={ENGINES[4]} />
          </div>
        </div>

        <div className="mt-12 flex flex-wrap gap-x-8 gap-y-3 font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">
          <span><span className="text-gold">●</span> 57 python files</span>
          <span><span className="text-gold">●</span> typed data bus</span>
          <span><span className="text-gold">●</span> error isolation</span>
          <span><span className="text-gold">●</span> threadpool stage 2</span>
          <span><span className="text-gold">●</span> e1 fatal · e2/3/4 graceful</span>
        </div>
      </div>
    </section>
  );
}

function StageLabel({ n, label }: { n: number; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">
      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-gold text-gold">{n}</span>
      <span>Stage {n} · {label}</span>
    </div>
  );
}

function Connector() {
  return (
    <div className="relative w-full h-px">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gold/60 to-transparent" />
      <div className="absolute right-0 top-1/2 -translate-y-1/2 text-gold">→</div>
    </div>
  );
}

function EngineCard({ e }: { e: typeof ENGINES[number] }) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      className="group relative bg-black/40 border border-terminal-line p-5 hover:border-gold/40 transition-colors"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: `hsl(var(--${e.color}))` }} />
          <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim">E{e.id}</span>
        </div>
        <span className="font-mono text-[10px] text-terminal-dim">~{e.duration}s</span>
      </div>
      <h3 className="font-serif-display text-2xl text-terminal-foreground leading-tight">{e.name}</h3>
      <p className="mt-2 text-xs text-terminal-dim leading-relaxed">{e.desc}</p>
      <div className="mt-5 pt-4 border-t border-terminal-line/60 flex items-center justify-between font-mono text-[9px] uppercase tracking-[0.25em] text-terminal-dim">
        <span>by {e.author}</span>
        <span className="text-gold/70">→ {e.writes}</span>
      </div>
      {/* signature corner */}
      <div className="absolute top-0 right-0 h-8 w-8 overflow-hidden">
        <div
          className="absolute -top-4 -right-4 h-8 w-8 rotate-45"
          style={{ background: `hsl(var(--${e.color}))` }}
        />
      </div>
    </motion.div>
  );
}

// ──────────────── THREE QUESTIONS ────────────────
function ThreeQuestions() {
  const items = [
    {
      n: "01",
      q: "What is it worth?",
      a: "DCF intrinsic value, relative valuation against peers, sensitivity to WACC and growth, reverse-DCF — synthesized into a single verdict: undervalued, fairly valued, or overvalued.",
      sig: "valuation",
    },
    {
      n: "02",
      q: "How risky is it?",
      a: "Market risk (beta, volatility, drawdown, VaR, Sharpe), financial health (Altman Z, interest coverage, debt ratios), and rule-based red-flag detection across six dimensions.",
      sig: "risk",
    },
    {
      n: "03",
      q: "What is management saying?",
      a: "NLP across earnings calls and 10-K filings. Sentiment scoring, key theme extraction, hedging-language detection — and a check: do the words match the numbers?",
      sig: "nlp",
    },
  ];
  return (
    <section className="bg-paper py-28 border-y border-foreground/10 relative">
      <CornerMarks />
      <div className="container max-w-6xl">
        <SectionHeader
          eyebrow="§ iii · the questions"
          title={<>Every memo answers<br /><span className="italic font-light">three questions.</span></>}
        />
        <div className="mt-16 divide-y divide-foreground/15 border-y border-foreground/15">
          {items.map((it, i) => (
            <motion.div
              key={it.n}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6, delay: i * 0.08 }}
              className="grid md:grid-cols-12 gap-6 py-10 group"
            >
              <div className="md:col-span-1 font-mono text-xs text-muted-foreground">{it.n}</div>
              <div className="md:col-span-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="inline-block h-2 w-2 rounded-full" style={{ background: `hsl(var(--sig-${it.sig}))` }} />
                  <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Engine {it.sig}</span>
                </div>
                <h3 className="font-serif-display text-3xl md:text-4xl tracking-tight text-ink leading-[1.05]">{it.q}</h3>
              </div>
              <div className="md:col-span-7 text-foreground/75 leading-relaxed text-[15px] md:pl-8 md:border-l border-foreground/10">
                {it.a}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ──────────────── REPORT PREVIEW ────────────────
function ReportPreview() {
  const sections = [
    { n: "01", t: "Business summary",   d: "Revenue model, market position, competitive landscape" },
    { n: "02", t: "Financial performance", d: "Revenue growth, margins, returns, efficiency trends" },
    { n: "03", t: "Valuation range",    d: "DCF, relative multiples, sensitivity, verdict" },
    { n: "04", t: "Key risks",          d: "Market risk, financial health, red flags" },
    { n: "05", t: "Investment thesis",  d: "Bull case, catalysts, why this matters now" },
    { n: "06", t: "Bear case",          d: "What could go wrong, downside scenarios" },
  ];

  return (
    <section className="bg-terminal text-terminal-foreground py-28 relative overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-[0.04]" />
      <div className="container max-w-7xl relative">
        <div className="grid md:grid-cols-12 gap-12 items-start">
          <div className="md:col-span-4">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4">§ iv · the output</div>
            <h2 className="font-serif-display text-5xl md:text-6xl leading-[0.95] tracking-tight">
              A complete<br /><span className="italic font-light text-gold">research memo.</span>
            </h2>
            <p className="mt-6 text-terminal-dim text-sm leading-relaxed max-w-sm">
              Six narrative sections. Generated in seconds. Exported as PDF.
              Every claim traceable to a numbered citation in the source data.
            </p>

            <div className="mt-8 space-y-2 font-mono text-[10px] uppercase tracking-[0.2em] text-terminal-dim">
              <Spec k="Format"  v="PDF · base64" />
              <Spec k="Pages"   v="4–6" />
              <Spec k="Engine"  v="ReportLab" />
              <Spec k="Author"  v="Naman" />
            </div>
          </div>

          <div className="md:col-span-8">
            <div className="bg-paper text-ink rounded-sm shadow-[0_30px_70px_-20px_hsl(var(--ink)/0.6)] overflow-hidden">
              {/* doc header */}
              <div className="flex items-center justify-between p-6 border-b border-foreground/15 bg-bone">
                <div>
                  <div className="font-serif-display text-xl text-ink">Apple Inc. — Equity Research Memo</div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground mt-1">
                    Generated 03 may 2026 · NASDAQ:AAPL · Technology
                  </div>
                </div>
                <div className="hidden md:flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
                  <span>EM-2026-0003</span>
                </div>
              </div>

              {/* verdict band */}
              <VerdictBand />

              {/* section grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 divide-x divide-y divide-foreground/10">
                {sections.map((s) => (
                  <div key={s.n} className="p-5 hover:bg-bone/60 transition-colors">
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-gold mb-2">{s.n}</div>
                    <div className="font-serif-display text-lg text-ink leading-snug">{s.t}</div>
                    <div className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{s.d}</div>
                  </div>
                ))}
              </div>

              {/* footer with charts */}
              <MiniCharts />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Spec({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between border-b border-terminal-line py-1.5">
      <span className="text-terminal-dim">{k}</span>
      <span className="text-terminal-foreground">{v}</span>
    </div>
  );
}

function VerdictBand() {
  return (
    <div className="p-6 border-b border-foreground/10">
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Verdict · valuation range</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-verdict-fair">Fairly valued</span>
      </div>
      <div className="relative h-2 rounded-full bg-bone overflow-hidden">
        <div className="absolute inset-y-0 left-0 w-1/3 bg-verdict-under/70" />
        <div className="absolute inset-y-0 left-1/3 w-1/3 bg-verdict-fair/70" />
        <div className="absolute inset-y-0 right-0 w-1/3 bg-verdict-over/70" />
        {/* marker */}
        <motion.div
          initial={{ left: "10%" }}
          whileInView={{ left: "52%" }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-5 w-5 rounded-full bg-ink border-2 border-paper shadow"
        />
      </div>
      <div className="flex justify-between mt-2 font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
        <span>Undervalued</span>
        <span>Fair</span>
        <span>Overvalued</span>
      </div>
    </div>
  );
}

function MiniCharts() {
  // synthetic deterministic data
  const bars = Array.from({ length: 24 }, (_, i) => 30 + Math.sin(i * 0.6) * 18 + i * 1.4);
  const max = Math.max(...bars);
  return (
    <div className="grid grid-cols-3 divide-x divide-foreground/10 border-t border-foreground/10">
      <div className="p-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Revenue · TTM</div>
        <div className="font-serif-display text-2xl text-ink mt-1">$394.3B</div>
        <div className="text-[10px] text-verdict-under font-mono mt-1">▲ 8.2% YoY</div>
        <div className="mt-3 flex items-end gap-[2px] h-10">
          {bars.map((b, i) => (
            <div key={i} className="flex-1 bg-ink/80" style={{ height: `${(b / max) * 100}%` }} />
          ))}
        </div>
      </div>
      <div className="p-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Altman Z · Health</div>
        <div className="font-serif-display text-2xl text-ink mt-1">5.84</div>
        <div className="text-[10px] text-verdict-under font-mono mt-1">Safe · low distress</div>
        <div className="mt-3 relative h-10">
          <svg viewBox="0 0 100 40" className="absolute inset-0 w-full h-full">
            <path d="M0,30 C20,28 30,12 50,15 C70,18 80,5 100,8" stroke="hsl(var(--sig-risk))" strokeWidth="1.5" fill="none" />
            <circle cx="100" cy="8" r="2" fill="hsl(var(--sig-risk))" />
          </svg>
        </div>
      </div>
      <div className="p-5">
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Earnings call · sentiment</div>
        <div className="font-serif-display text-2xl text-ink mt-1">+0.42</div>
        <div className="text-[10px] text-verdict-fair font-mono mt-1">Cautiously optimistic</div>
        <div className="mt-3 grid grid-cols-12 gap-[2px] h-10">
          {Array.from({ length: 36 }, (_, i) => {
            const v = Math.sin(i * 0.5) * 0.5 + 0.3;
            return <div key={i} style={{ background: v > 0 ? `hsl(var(--sig-nlp) / ${0.4 + v})` : `hsl(var(--verdict-over) / 0.4)` }} />;
          })}
        </div>
      </div>
    </div>
  );
}

// ──────────────── METHOD / DAG ────────────────
function MethodSection() {
  return (
    <section className="bg-paper py-28 border-y border-foreground/10 relative">
      <div className="container max-w-7xl">
        <SectionHeader
          eyebrow="§ v · the method"
          title={<>Orchestrator<br /><span className="italic font-light">+ data bus.</span></>}
          desc="Engines never call each other. They read from a typed shared context and write back. The orchestrator resolves a DAG and dispatches stages."
        />

        <div className="mt-20 grid md:grid-cols-12 gap-12 items-start">
          {/* DAG */}
          <div className="md:col-span-7">
            <div className="bg-terminal text-terminal-foreground p-8 rounded-sm relative overflow-hidden">
              <div className="absolute inset-0 grid-bg opacity-[0.06]" />
              <div className="relative">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-terminal-dim mb-6">
                  → resolve_stages(DAG) → ThreadPoolExecutor
                </div>
                <DAGDiagram />
              </div>
            </div>
          </div>

          {/* Code excerpt */}
          <div className="md:col-span-5">
            <div className="bg-terminal text-terminal-foreground p-6 rounded-sm font-mono text-[12px] leading-relaxed">
              <div className="text-terminal-dim mb-3 text-[10px] uppercase tracking-[0.25em]">pipeline/orchestrator.py</div>
              <pre className="whitespace-pre-wrap text-terminal-foreground/90">
<span className="text-gold">class</span> <span className="text-sig-nlp">BaseEngine</span>(ABC):
    name: <span className="text-sig-data">str</span>
    requires: list[<span className="text-sig-data">str</span>]
    produces: <span className="text-sig-data">str</span>

    <span className="text-gold">def</span> <span className="text-sig-valuation">run</span>(self, ctx: dict) <span className="text-terminal-dim">→</span> dict:
        ...

<span className="text-terminal-dim"># E1 fatal · E2/3/4 graceful</span>
<span className="text-terminal-dim"># Stage 2 runs in parallel</span>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function DAGDiagram() {
  const stage1 = ENGINES.filter((e) => e.stage === 1);
  const stage2 = ENGINES.filter((e) => e.stage === 2);
  const stage3 = ENGINES.filter((e) => e.stage === 3);
  const Node = ({ e }: { e: typeof ENGINES[number] }) => (
    <div className="flex items-center gap-2 px-3 py-2 border border-terminal-line bg-black/40 min-w-[140px]">
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: `hsl(var(--${e.color}))` }} />
      <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-terminal-foreground">E{e.id} · {e.name}</span>
    </div>
  );
  return (
    <div className="grid grid-cols-3 gap-6 items-center">
      <div className="space-y-2">
        <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-gold mb-1">Stage 1</div>
        {stage1.map((e) => <Node key={e.id} e={e} />)}
      </div>
      <div className="space-y-2 relative">
        <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-gold mb-1">Stage 2 · parallel</div>
        {stage2.map((e) => <Node key={e.id} e={e} />)}
        {/* fan in lines */}
        <svg className="absolute -left-6 top-0 h-full w-6 pointer-events-none" preserveAspectRatio="none" viewBox="0 0 24 100">
          <path d="M0,50 C12,50 12,18 24,18" stroke="hsl(var(--gold) / 0.4)" fill="none" />
          <path d="M0,50 L24,50" stroke="hsl(var(--gold) / 0.4)" fill="none" />
          <path d="M0,50 C12,50 12,82 24,82" stroke="hsl(var(--gold) / 0.4)" fill="none" />
        </svg>
        <svg className="absolute -right-6 top-0 h-full w-6 pointer-events-none" preserveAspectRatio="none" viewBox="0 0 24 100">
          <path d="M0,18 C12,18 12,50 24,50" stroke="hsl(var(--gold) / 0.4)" fill="none" />
          <path d="M0,50 L24,50" stroke="hsl(var(--gold) / 0.4)" fill="none" />
          <path d="M0,82 C12,82 12,50 24,50" stroke="hsl(var(--gold) / 0.4)" fill="none" />
        </svg>
      </div>
      <div className="space-y-2">
        <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-gold mb-1">Stage 3</div>
        {stage3.map((e) => <Node key={e.id} e={e} />)}
      </div>
    </div>
  );
}

// ──────────────── BENCH ────────────────
function Bench() {
  const stats = [
    { k: "27.4", u: "s", l: "End-to-end p50 latency" },
    { k: "5", u: "engines", l: "Running in 3 ordered stages" },
    { k: "57", u: "files", l: "Backend Python modules" },
    { k: "6", u: "sections", l: "Per generated memo" },
  ];
  return (
    <section className="bg-ink text-paper py-20 relative">
      <div className="container max-w-7xl">
        <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-paper/10 border-y border-paper/10 py-8">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              className="px-6 first:pl-0"
            >
              <div className="flex items-baseline gap-2">
                <span className="font-serif-display text-6xl md:text-7xl tracking-tight">{s.k}</span>
                <span className="font-mono text-xs uppercase tracking-[0.2em] text-paper/50">{s.u}</span>
              </div>
              <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.25em] text-paper/50">{s.l}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ──────────────── CTA / FINAL ────────────────
function FinalCTA() {
  return (
    <section className="bg-paper py-32 text-center relative overflow-hidden">
      <CornerMarks />
      <div className="container max-w-4xl">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-6">§ vi · colophon</div>
        <h2 className="font-serif-display text-6xl md:text-8xl leading-[0.9] tracking-tight text-ink">
          One ticker.<br />
          <span className="italic font-light">One minute.</span><br />
          One complete answer.
        </h2>
        <p className="mt-8 text-foreground/60 max-w-md mx-auto">
          No signup. No paywall. Just type a symbol and read what the engines wrote.
        </p>

        <a
          href="#top"
          className="group mt-12 inline-flex items-center gap-4 px-6 py-4 bg-ink text-paper hover:bg-gold hover:text-ink transition-colors font-mono text-xs uppercase tracking-[0.3em]"
        >
          <span className="font-serif-display text-base normal-case tracking-normal">$</span>
          Enter ticker
          <span className="inline-block transition-transform group-hover:translate-x-1">→</span>
        </a>
      </div>
    </section>
  );
}

// ──────────────── SHARED ────────────────
function SectionHeader({ eyebrow, title, desc, dark }: any) {
  return (
    <div className="grid md:grid-cols-12 gap-6 items-end">
      <div className="md:col-span-8">
        <div className={`font-mono text-[10px] uppercase tracking-[0.3em] mb-5 ${dark ? "text-gold" : "text-gold"}`}>
          {eyebrow}
        </div>
        <h2 className={`font-serif-display text-5xl md:text-7xl leading-[0.92] tracking-tight ${dark ? "text-terminal-foreground" : "text-ink"}`}>
          {title}
        </h2>
      </div>
      {desc && (
        <p className={`md:col-span-4 text-sm leading-relaxed ${dark ? "text-terminal-dim" : "text-foreground/65"}`}>
          {desc}
        </p>
      )}
    </div>
  );
}

// ──────────────── NAV ────────────────
function Nav() {
  return (
    <nav className="sticky top-0 z-50 bg-paper/90 backdrop-blur border-b border-foreground/10">
      <div className="container max-w-7xl flex items-center justify-between py-4">
        <a href="#top" className="flex items-center gap-2.5">
          <span className="inline-block h-6 w-6 bg-ink relative">
            <span className="absolute inset-1 bg-gold" />
          </span>
          <span className="font-serif-display text-xl tracking-tight text-ink">equimind<span className="text-gold">.</span></span>
        </a>
        <div className="hidden md:flex items-center gap-8 font-mono text-[11px] uppercase tracking-[0.25em] text-foreground/70">
          <a href="#engines" className="hover:text-ink">Engines</a>
          <a href="#method" className="hover:text-ink">Method</a>
          <a href="#memo" className="hover:text-ink">Memo</a>
          <Link to="/login" className="hover:text-ink">Sign in</Link>
          <Link to="/signup" className="inline-flex items-center gap-2 px-3 py-1.5 bg-ink text-paper hover:bg-gold hover:text-ink transition-colors">
            Run a ticker →
          </Link>
        </div>
      </div>
    </nav>
  );
}

// ──────────────── FOOTER ────────────────
function Footer() {
  return (
    <footer className="bg-ink text-paper/70 py-12">
      <div className="container max-w-7xl">
        <div className="grid md:grid-cols-12 gap-8 items-end">
          <div className="md:col-span-6">
            <div className="font-serif-display text-3xl text-paper">
              equimind<span className="text-gold">.</span>
            </div>
            <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.25em] text-paper/50">
              Equity research, computed. · Vol. I · MMXXVI
            </p>
          </div>
          <div className="md:col-span-6 grid grid-cols-2 gap-4 font-mono text-[10px] uppercase tracking-[0.25em]">
            <div>
              <div className="text-paper/40 mb-2">Built by</div>
              <div className="space-y-1 text-paper/80">
                <div>Siddharth · valuation, risk</div>
                <div>Divyansh · financial data</div>
                <div>Annant · NLP intelligence</div>
                <div>Naman · report engine</div>
              </div>
            </div>
            <div>
              <div className="text-paper/40 mb-2">Stack</div>
              <div className="space-y-1 text-paper/80">
                <div>FastAPI · Python</div>
                <div>React · Vite · Framer</div>
                <div>Alpha Vantage · Finnhub</div>
                <div>EDGAR · FMP</div>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-paper/10 flex flex-wrap items-center justify-between font-mono text-[10px] uppercase tracking-[0.25em] text-paper/40">
          <span>© 2026 equimind.app · all rights reserved</span>
          <span>Not investment advice · Educational use</span>
        </div>
      </div>
    </footer>
  );
}

// ──────────────── PAGE ────────────────
export default function Index() {
  return (
    <main id="top" className="bg-paper">
      <Nav />
      <Hero />
      <TickerMarquee />
      <section id="engines"><EnginesSection /></section>
      <ThreeQuestions />
      <section id="memo"><ReportPreview /></section>
      <section id="method"><MethodSection /></section>
      <Bench />
      <FinalCTA />
      <Footer />
    </main>
  );
}
