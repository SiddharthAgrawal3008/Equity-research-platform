import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function Products() {
  return (
    <>
      <section className="container py-20 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Products</div>
          <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
            One platform. The whole research stack.
          </h1>
          <p className="mt-5 text-base text-muted-foreground">
            EquiMind ships a focused suite of research tools — built modularly so
            you can adopt one engine or the entire workflow.
          </p>
        </div>
      </section>

      <section className="container pb-24">
        <Card className="overflow-hidden border-border bg-surface shadow-elevated">
          <div className="grid gap-0 lg:grid-cols-2">
            <div className="p-8 lg:p-12">
              <Badge className="mb-4 bg-accent-soft text-accent hover:bg-accent-soft">Flagship</Badge>
              <h2 className="font-display text-3xl font-semibold tracking-tight">
                Equity Research Platform
              </h2>
              <p className="mt-3 text-muted-foreground">
                The complete pipeline: financial data ingestion, valuation,
                risk scoring, NLP sentiment and a final IB-style investment memo
                — all in a single browser session.
              </p>
              <ul className="mt-6 space-y-2.5 text-sm">
                {[
                  "DCF + Monte Carlo + sensitivity analysis",
                  "Beta, VaR, Sharpe, Altman Z, max drawdown",
                  "10-K & earnings call sentiment scoring",
                  "Auto-generated investment memo with bear/bull",
                  "Export to PDF / Markdown / CSV",
                ].map((f) => (
                  <li key={f} className="flex items-start gap-2 text-foreground/80">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-bull" />
                    {f}
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex gap-3">
                <Button asChild variant="hero" size="lg">
                  <Link to="/app">
                    Launch App <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link to="/contact">Book a demo</Link>
                </Button>
              </div>
            </div>
            <div className="relative bg-gradient-navy p-8 lg:p-12">
              <div className="terminal-grid absolute inset-0 opacity-30" />
              <div className="relative space-y-3">
                {[
                  { l: "AAPL", v: "$198.40", c: "+12.3%", b: "bull" },
                  { l: "TSLA", v: "$214.10", c: "-8.1%", b: "bear" },
                  { l: "NVDA", v: "$162.20", c: "+17.4%", b: "bull" },
                  { l: "JPM", v: "$229.85", c: "+3.6%", b: "bull" },
                ].map((row) => (
                  <div
                    key={row.l}
                    className="flex items-center justify-between rounded-lg border border-sidebar-border bg-sidebar-accent/40 px-4 py-3 backdrop-blur"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono-num text-sm font-semibold text-primary-foreground">{row.l}</span>
                      <span className="text-xs text-primary-foreground/50">Intrinsic</span>
                    </div>
                    <div className="flex items-center gap-3 font-mono-num text-sm">
                      <span className="text-primary-foreground">{row.v}</span>
                      <span className={row.b === "bull" ? "text-bull" : "text-bear"}>{row.c}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {[
            { name: "EquiMind Screener", desc: "Multi-factor screening across 8,000+ equities." },
            { name: "EquiMind API", desc: "Programmatic access to all 5 engines for desks & funds." },
            { name: "EquiMind Insights", desc: "Daily AI-curated theses across sectors and themes." },
          ].map((p) => (
            <Card key={p.name} className="border-border bg-surface p-6 shadow-card">
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-accent" /> Coming soon
              </div>
              <h3 className="text-lg font-semibold">{p.name}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{p.desc}</p>
            </Card>
          ))}
        </div>
      </section>
    </>
  );
}
