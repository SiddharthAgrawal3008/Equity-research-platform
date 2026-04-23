import { motion } from "framer-motion";

const tickers = [
  { sym: "AAPL", price: "229.87", chg: "+1.24%" },
  { sym: "TSLA", price: "248.12", chg: "-0.86%" },
  { sym: "NVDA", price: "138.40", chg: "+2.41%" },
  { sym: "MSFT", price: "428.55", chg: "+0.62%" },
  { sym: "GOOGL", price: "172.30", chg: "+0.98%" },
  { sym: "META", price: "596.21", chg: "-0.34%" },
  { sym: "AMZN", price: "204.18", chg: "+1.07%" },
  { sym: "JPM", price: "238.74", chg: "+0.51%" },
  { sym: "BRK.B", price: "459.10", chg: "-0.12%" },
];

export const TickerTape = () => {
  const items = [...tickers, ...tickers];
  return (
    <div className="relative overflow-hidden border-y border-border bg-primary py-3">
      <div className="flex animate-ticker whitespace-nowrap">
        {items.map((t, i) => (
          <div key={i} className="flex shrink-0 items-center gap-3 px-6 font-mono-num text-xs text-primary-foreground/80">
            <span className="font-semibold text-primary-foreground">{t.sym}</span>
            <span>{t.price}</span>
            <span className={t.chg.startsWith("+") ? "text-bull" : "text-bear"}>{t.chg}</span>
            <span className="text-primary-foreground/30">•</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const HeroChartBg = () => {
  // Animated SVG line chart background — subtle institutional vibe
  const points = [10, 30, 22, 45, 38, 60, 52, 78, 70, 95, 85, 110, 100, 130];
  const width = 1200;
  const step = width / (points.length - 1);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${160 - p}`).join(" ");
  const area = `${path} L ${width} 160 L 0 160 Z`;

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-hero" />
      <div className="absolute inset-0 grid-bg opacity-60" />
      <svg
        className="absolute bottom-0 left-0 right-0 h-48 w-full"
        viewBox="0 0 1200 160"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity="0.25" />
            <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity="0" />
          </linearGradient>
        </defs>
        <motion.path
          d={area}
          fill="url(#areaGrad)"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.4 }}
        />
        <motion.path
          d={path}
          fill="none"
          stroke="hsl(var(--accent))"
          strokeWidth={2}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.8, ease: "easeOut" }}
        />
      </svg>
    </div>
  );
};
