import { Link } from "react-router-dom";
import { ArrowRight, GraduationCap, LineChart, Briefcase, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const personas = [
  {
    icon: Users,
    name: "Retail Investors",
    pain: "Buried in noise. No time to read 200-page 10-Ks.",
    solve: "Get a structured, plain-English investment memo on any ticker in under a minute.",
  },
  {
    icon: GraduationCap,
    name: "Finance Students",
    pain: "Need to learn DCF, Monte Carlo and sentiment analysis hands-on.",
    solve: "See every assumption, formula and chart — auditable models you can learn from.",
  },
  {
    icon: LineChart,
    name: "Equity Analysts",
    pain: "Repetitive data wrangling stalls real analysis.",
    solve: "Automate ingestion and modeling. Spend your time on thesis, not on plumbing.",
  },
  {
    icon: Briefcase,
    name: "Portfolio Managers",
    pain: "Coverage gaps across mid-cap and emerging markets.",
    solve: "Instant baseline coverage on any name, with risk and sentiment overlays.",
  },
];

export default function Solutions() {
  return (
    <>
      <section className="container py-20 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Solutions</div>
          <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
            Built for everyone who reads research.
          </h1>
          <p className="mt-5 text-base text-muted-foreground">
            From your first valuation course to a $1B portfolio — EquiMind
            scales with how you work.
          </p>
        </div>
      </section>

      <section className="container pb-24">
        <div className="grid gap-6 md:grid-cols-2">
          {personas.map((p) => (
            <Card key={p.name} className="group border-border bg-surface p-8 shadow-card transition-shadow hover:shadow-elevated">
              <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-accent-soft text-accent">
                <p.icon className="h-5 w-5" />
              </div>
              <h3 className="text-xl font-semibold">{p.name}</h3>
              <div className="mt-5 space-y-4 text-sm">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Pain</div>
                  <p className="mt-1 text-foreground/80">{p.pain}</p>
                </div>
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-accent">How EquiMind helps</div>
                  <p className="mt-1 text-foreground/80">{p.solve}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div className="mt-16 text-center">
          <Button asChild variant="hero" size="lg">
            <Link to="/app">
              See it for your workflow <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>
    </>
  );
}
