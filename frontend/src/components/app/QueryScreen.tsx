import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Search, Sparkles, TrendingUp, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TICKERS } from "@/lib/mockData";

export const QueryScreen = () => {
  const [value, setValue] = useState("");
  const navigate = useNavigate();

  const submit = (t: string) => {
    if (!t.trim()) return;
    navigate(`/app/research/${t.trim().toUpperCase()}`);
  };

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-hidden px-4 py-12">
      <div className="terminal-grid pointer-events-none absolute inset-0 opacity-30" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-hero" />

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative w-full max-w-2xl"
      >
        <div className="mb-8 text-center">
          <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-accent" /> 5 engines · live
          </div>
          <h1 className="text-balance font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            What stock do you want to research?
          </h1>
          <p className="mt-3 text-sm text-muted-foreground">
            Get a complete DCF valuation, risk analysis, NLP sentiment, and
            investment memo in seconds.
          </p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(value);
          }}
          className="relative"
        >
          <div className="flex items-center gap-2 rounded-xl border border-border bg-surface p-2 shadow-elevated focus-within:border-accent focus-within:shadow-glow">
            <Search className="ml-2 h-4 w-4 text-muted-foreground" />
            <Input
              value={value}
              onChange={(e) => setValue(e.target.value.toUpperCase())}
              placeholder="Enter a ticker symbol (e.g., AAPL, TSLA, MSFT)"
              className="border-0 bg-transparent font-mono-num text-base shadow-none focus-visible:ring-0"
              autoFocus
            />
            <Button type="submit" variant="hero" size="lg" disabled={!value.trim()}>
              Analyze <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </form>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          <span className="text-xs text-muted-foreground">Try:</span>
          {TICKERS.map((t) => (
            <button
              key={t}
              onClick={() => submit(t)}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 font-mono-num text-xs font-medium text-foreground transition-colors hover:border-accent hover:bg-accent-soft hover:text-accent"
            >
              <TrendingUp className="h-3 w-3" /> {t}
            </button>
          ))}
        </div>

        <div className="mt-10 flex items-center gap-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
        </div>

        <button
          onClick={() => navigate("/app/clients")}
          className="mt-4 flex w-full items-center gap-3 rounded-xl border border-border bg-surface p-4 text-left transition-all hover:border-accent/60 hover:shadow-card"
        >
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-navy text-primary-foreground">
            <Users className="h-4 w-4" />
          </span>
          <span className="flex-1">
            <span className="block text-sm font-semibold text-foreground">Open private client workspace</span>
            <span className="block text-xs text-muted-foreground">
              Upload Excel, PDFs and transcripts to generate or verify analysis for your clients.
            </span>
          </span>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
        </button>
      </motion.div>
    </div>
  );
};
