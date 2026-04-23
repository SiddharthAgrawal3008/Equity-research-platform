import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";

const STEPS = [
  "Fetching financial data...",
  "Running valuation models...",
  "Computing risk metrics...",
  "Analyzing sentiment...",
  "Generating investment memo...",
];

interface Props {
  ticker: string;
  onComplete: () => void;
}

export const LoadingScreen = ({ ticker, onComplete }: Props) => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step >= STEPS.length) {
      const t = setTimeout(onComplete, 350);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setStep((s) => s + 1), 520);
    return () => clearTimeout(t);
  }, [step, onComplete]);

  const progress = Math.min(100, (step / STEPS.length) * 100);

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-hidden px-4 py-12">
      <div className="terminal-grid pointer-events-none absolute inset-0 opacity-30" />
      <div className="relative w-full max-w-md">
        <div className="text-center">
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">Analyzing</div>
          <div className="mt-2 font-display text-5xl font-semibold tracking-tight text-foreground">
            {ticker}
          </div>
        </div>

        <div className="mt-10 h-1.5 overflow-hidden rounded-full bg-surface-muted">
          <motion.div
            className="h-full bg-gradient-accent"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
        </div>

        <ul className="mt-8 space-y-3">
          {STEPS.map((label, i) => {
            const done = i < step;
            const active = i === step;
            return (
              <motion.li
                key={label}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-center gap-3 text-sm"
              >
                <span className="flex h-5 w-5 items-center justify-center">
                  {done ? (
                    <CheckCircle2 className="h-5 w-5 text-bull" />
                  ) : active ? (
                    <Loader2 className="h-4 w-4 animate-spin text-accent" />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-muted" />
                  )}
                </span>
                <span
                  className={
                    done
                      ? "text-muted-foreground line-through"
                      : active
                      ? "text-foreground"
                      : "text-muted-foreground/60"
                  }
                >
                  {label}
                </span>
              </motion.li>
            );
          })}
        </ul>
      </div>
    </div>
  );
};
