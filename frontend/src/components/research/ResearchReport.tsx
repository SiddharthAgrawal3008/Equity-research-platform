import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, BarChart3, Brain, FileText, Layers, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getCompany, type CompanyData } from "@/lib/mockData";
import { OverviewTab } from "@/components/research/OverviewTab";
import { ValuationTab } from "@/components/research/ValuationTab";
import { RiskTab } from "@/components/research/RiskTab";
import { SentimentTab } from "@/components/research/SentimentTab";
import { MemoTab } from "@/components/research/MemoTab";
import { VerificationPanel } from "@/components/research/VerificationPanel";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "overview", label: "Overview", icon: Layers },
  { id: "valuation", label: "Valuation", icon: BarChart3 },
  { id: "risk", label: "Risk & Health", icon: ShieldAlert },
  { id: "sentiment", label: "NLP Sentiment", icon: Brain },
  { id: "memo", label: "Investment Memo", icon: FileText },
] as const;

type TabId = (typeof TABS)[number]["id"];

export const ResearchReport = ({
  ticker: tickerProp,
  data,
  fetchError: _fetchError,
}: {
  ticker?: string;
  data?: CompanyData | null;
  fetchError?: string | null;
}) => {
  const params = useParams();
  const ticker = (tickerProp ?? params.ticker ?? "").toUpperCase();
  const c = data ?? getCompany(ticker);
  const [tab, setTab] = useState<TabId>("overview");

  if (!c) {
    return (
      <div className="container flex flex-1 items-center justify-center py-24">
        <div className="max-w-md text-center">
          <div className="font-display text-5xl font-semibold text-muted-foreground">404</div>
          <h2 className="mt-4 font-display text-xl font-semibold">No coverage for "{ticker}"</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            We couldn't find data for that symbol. Try a different ticker.
          </p>
          <Button asChild variant="hero" className="mt-6">
            <Link to="/app"><ArrowLeft className="h-4 w-4" /> Back to query</Link>
          </Button>
        </div>
      </div>
    );
  }

  const ratingColor =
    c.rating === "BUY" ? "bg-bull text-bull-foreground" :
    c.rating === "SELL" ? "bg-bear text-bear-foreground" :
    "bg-neutral text-neutral-foreground";

  return (
    <div className="container flex-1 py-6 lg:py-8">
      <div className="mb-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/app"><ArrowLeft className="h-4 w-4" /> New search</Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Sidebar */}
        <aside className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5 shadow-card">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{c.name}</div>
            <div className="mt-1 flex items-center justify-between">
              <span className="font-display text-2xl font-semibold">{c.ticker}</span>
              <Badge className={cn("hover:opacity-100", ratingColor)}>{c.rating}</Badge>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="font-mono-num text-2xl font-semibold">${c.price.toFixed(2)}</span>
              <span className={`font-mono-num text-sm ${c.change >= 0 ? "text-bull" : "text-bear"}`}>
                {c.change >= 0 ? "+" : ""}{c.change.toFixed(2)}%
              </span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">Mkt Cap {c.marketCap}</div>
          </div>

          <nav className="rounded-xl border border-border bg-card p-2 shadow-card lg:sticky lg:top-20">
            {TABS.map((t) => {
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <t.icon className="h-4 w-4" />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </nav>

          <VerificationPanel />
        </aside>

        {/* Main */}
        <main className="min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
            >
              {tab === "overview" && <OverviewTab c={c} />}
              {tab === "valuation" && <ValuationTab c={c} />}
              {tab === "risk" && <RiskTab c={c} />}
              {tab === "sentiment" && <SentimentTab c={c} />}
              {tab === "memo" && <MemoTab c={c} />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
