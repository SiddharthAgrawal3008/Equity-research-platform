import { Linkedin } from "lucide-react";
import { Card } from "@/components/ui/card";

const values = [
  { v: "Accuracy", d: "Auditable models. Every number traceable to its source." },
  { v: "Speed", d: "From ticker to memo in seconds, not days." },
  { v: "Transparency", d: "Show the assumptions. Show the math. Always." },
  { v: "Accessibility", d: "Institutional tools, in everyone's browser." },
];

const team = [
  { name: "Divyansh", role: "Engine 1 — Financial Data", bio: "Builds the data ingestion layer powering every downstream model." },
  { name: "Siddharth", role: "Engine 2 + 3 — Valuation & Risk", bio: "Owns DCF, Monte Carlo and the firm's risk-scoring framework." },
  { name: "Annant", role: "Engine 4 — NLP Intelligence", bio: "Designs the language models that read 10-Ks so you don't have to." },
  { name: "Naman", role: "Engine 5 — Investment Memos", bio: "Synthesises the engines into IB-grade research notes, automatically." },
];

export default function About() {
  return (
    <>
      <section className="container py-20 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">About</div>
          <h1 className="mt-3 text-balance font-display text-4xl font-semibold tracking-tight sm:text-5xl">
            We're building the Bloomberg Terminal for the AI era.
          </h1>
          <p className="mt-6 text-base text-muted-foreground">
            EquiMind exists because deep equity research shouldn't be locked
            behind six-figure subscriptions. We're a small team of engineers and
            analysts rebuilding the research workflow with modern AI — open,
            fast, and rigorous.
          </p>
        </div>
      </section>

      <section className="border-y border-border bg-surface-muted py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-semibold tracking-tight">Our values</h2>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {values.map((v) => (
              <Card key={v.v} className="border-border bg-surface p-6 shadow-card">
                <div className="font-display text-lg font-semibold">{v.v}</div>
                <p className="mt-2 text-sm text-muted-foreground">{v.d}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="team" className="container py-24">
        <div className="mx-auto max-w-2xl text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">The team</div>
          <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">Behind the engines</h2>
          <p className="mt-4 text-muted-foreground">
            Four engineers, five engines, one mission.
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {team.map((t) => (
            <Card key={t.name} className="overflow-hidden border-border bg-surface shadow-card">
              <div className="flex h-32 items-center justify-center bg-gradient-navy">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-surface text-2xl font-display font-semibold text-primary shadow-elevated">
                  {t.name.charAt(0)}
                </div>
              </div>
              <div className="space-y-2 p-5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{t.name}</h3>
                  <a href="#" className="text-muted-foreground hover:text-accent">
                    <Linkedin className="h-4 w-4" />
                  </a>
                </div>
                <div className="text-xs font-medium text-accent">{t.role}</div>
                <p className="text-sm text-muted-foreground">{t.bio}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>
    </>
  );
}
