import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Brain,
  FileText,
  Calculator,
  ShieldAlert,
  Database,
  Sparkles,
  Search,
  Cpu,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HeroChartBg, TickerTape } from "@/components/marketing/HeroVisuals";

const engines = [
  {
    icon: Database,
    title: "Financial Data Engine",
    desc: "Income statements, balance sheets, cash flows, TTM and seasonally-adjusted normalization across 30+ exchanges.",
  },
  {
    icon: Calculator,
    title: "Valuation Engine",
    desc: "DCF intrinsic value, relative multiples (EV/EBITDA, P/E, P/B), sensitivity grids and Monte Carlo simulation.",
  },
  {
    icon: ShieldAlert,
    title: "Risk & Financial Health",
    desc: "Beta, Value-at-Risk, Sharpe, Altman Z-score, and max drawdown — quantified balance-sheet stress signals.",
  },
  {
    icon: Brain,
    title: "NLP Intelligence Engine",
    desc: "Sentiment from 10-Ks, earnings calls, management tone scoring and red-flag keyword detection.",
  },
  {
    icon: FileText,
    title: "Investment Memo Generator",
    desc: "An IB-style research note: thesis, bear case, valuation range, key risks — formatted, exportable.",
  },
];

const steps = [
  { icon: Search, title: "Enter a ticker", desc: "AAPL, TSLA, NVDA — any listed equity." },
  { icon: Cpu, title: "5 engines run in parallel", desc: "Data, valuation, risk, NLP and memo synthesis." },
  { icon: FileText, title: "Get a full report", desc: "Institutional-grade memo in under 30 seconds." },
];

export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden">
        <HeroChartBg />
        <div className="container relative pb-24 pt-20 sm:pt-28 lg:pt-36">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mx-auto max-w-4xl text-center"
          >
            <Badge variant="outline" className="mb-6 gap-1.5 rounded-full border-border bg-surface/80 px-3 py-1 backdrop-blur">
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              <span className="text-xs font-medium">Now powering 5 AI research engines</span>
            </Badge>
            <h1 className="text-balance font-display text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Institutional-Grade Equity Research,{" "}
              <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent">
                Automated.
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-balance text-base text-muted-foreground sm:text-lg">
              From raw ticker to full investment memo in seconds. DCF models,
              risk scoring, NLP sentiment analysis — all in one platform.
            </p>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button asChild variant="hero" size="lg">
                <Link to="/login">
                  Get Started Free <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <a href="#how">See How It Works</a>
              </Button>
            </div>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
              {["DCF + Monte Carlo", "NLP Sentiment", "Auto Investment Memo"].map((b) => (
                <span key={b} className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-bull" /> {b}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Mock terminal preview */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="mx-auto mt-16 max-w-5xl"
          >
            <PreviewTerminal />
          </motion.div>
        </div>
      </section>

      <TickerTape />

      {/* HOW IT WORKS */}
      <section id="how" className="py-24 sm:py-32">
        <div className="container">
          <SectionHeader
            kicker="Workflow"
            title="From ticker to thesis in three steps"
            subtitle="Built for analysts who need institutional rigor without institutional overhead."
          />
          <div className="relative mt-16 grid gap-8 md:grid-cols-3">
            <div className="absolute left-[12%] right-[12%] top-12 hidden h-px border-t border-dashed border-border md:block" />
            {steps.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="relative"
              >
                <Card className="h-full border-border bg-surface p-6 shadow-card">
                  <div className="mb-4 flex items-center gap-3">
                    <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <s.icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono-num text-xs font-semibold text-muted-foreground">
                      0{i + 1}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">{s.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{s.desc}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES — 5 ENGINES */}
      <section className="bg-surface-muted py-24 sm:py-32">
        <div className="container">
          <SectionHeader
            kicker="The Platform"
            title="Five engines. One complete research report."
            subtitle="Each engine is purpose-built and independently auditable. Together they form a synthesised, IB-grade memo."
          />
          <div className="mt-16 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {engines.map((e, i) => (
              <motion.div
                key={e.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.06 }}
              >
                <Card className="group h-full border-border bg-surface p-7 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-elevated">
                  <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                    <e.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-semibold text-foreground">
                    Engine {i + 1} — {e.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{e.desc}</p>
                  <a
                    href="#"
                    className="mt-5 inline-flex items-center gap-1 text-xs font-semibold text-accent opacity-70 group-hover:opacity-100"
                  >
                    Learn more <ArrowRight className="h-3.5 w-3.5" />
                  </a>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="border-y border-border bg-primary py-20 text-primary-foreground">
        <div className="container grid gap-10 sm:grid-cols-3">
          {[
            { v: "5", l: "AI research engines" },
            { v: "10+", l: "Valuation metrics" },
            { v: "<30s", l: "Full memo generation" },
          ].map((s) => (
            <div key={s.l} className="text-center">
              <div className="font-display text-5xl font-semibold tracking-tight text-primary-foreground">
                {s.v}
              </div>
              <div className="mt-2 text-sm text-primary-foreground/70">{s.l}</div>
            </div>
          ))}
        </div>
      </section>

    </>
  );
}

const SectionHeader = ({
  kicker,
  title,
  subtitle,
  align = "center",
}: {
  kicker: string;
  title: string;
  subtitle?: string;
  align?: "center" | "left";
}) => (
  <div className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">{kicker}</div>
    <h2 className="mt-3 text-balance font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
      {title}
    </h2>
    {subtitle && <p className="mt-4 text-base text-muted-foreground">{subtitle}</p>}
  </div>
);

const PreviewTerminal = () => (
  <div className="relative">
    <div className="absolute -inset-6 rounded-3xl bg-gradient-accent opacity-15 blur-3xl" />
    <Card className="relative overflow-hidden border-border bg-primary text-primary-foreground shadow-elevated">
      <div className="flex items-center justify-between border-b border-sidebar-border px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-bear/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-neutral/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-bull/70" />
        </div>
        <span className="font-mono-num text-[11px] text-primary-foreground/50">equimind.app — research session</span>
        <span className="font-mono-num text-[11px] text-bull">● live</span>
      </div>
      <div className="grid gap-0 lg:grid-cols-[200px_1fr]">
        <div className="border-b border-sidebar-border bg-sidebar p-4 text-xs lg:border-b-0 lg:border-r">
          <div className="text-[10px] uppercase tracking-wider text-primary-foreground/50">Report</div>
          <div className="mt-2 space-y-1.5">
            {["Overview", "Valuation", "Risk & Health", "Sentiment", "Memo"].map((t, i) => (
              <div
                key={t}
                className={`rounded px-2 py-1.5 ${
                  i === 1 ? "bg-accent text-accent-foreground" : "text-primary-foreground/70"
                }`}
              >
                {t}
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4 p-6">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-[11px] uppercase tracking-wider text-primary-foreground/60">Apple Inc.</div>
              <div className="font-display text-3xl font-semibold">AAPL</div>
            </div>
            <Badge className="bg-bull text-bull-foreground hover:bg-bull">BUY · 12.3% upside</Badge>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { l: "Intrinsic Value", v: "$198.40" },
              { l: "Current Price", v: "$176.85" },
              { l: "WACC", v: "8.4%" },
            ].map((m) => (
              <div key={m.l} className="rounded-md border border-sidebar-border bg-sidebar-accent/40 p-3">
                <div className="text-[10px] uppercase tracking-wider text-primary-foreground/60">{m.l}</div>
                <div className="mt-1 font-mono-num text-base font-semibold text-primary-foreground">{m.v}</div>
              </div>
            ))}
          </div>
          <div className="rounded-md border border-sidebar-border bg-sidebar-accent/30 p-4">
            <div className="mb-2 text-[10px] uppercase tracking-wider text-primary-foreground/60">DCF Sensitivity (g vs WACC)</div>
            <div className="grid grid-cols-5 gap-1">
              {Array.from({ length: 25 }).map((_, i) => {
                const intensity = 0.15 + ((i * 37) % 100) / 130;
                return (
                  <div
                    key={i}
                    className="h-6 rounded-sm"
                    style={{ background: `hsl(var(--accent) / ${intensity.toFixed(2)})` }}
                  />
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </Card>
  </div>
);
