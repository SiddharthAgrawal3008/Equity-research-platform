import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";

interface HistoryItem {
  id: string;
  ticker: string;
  company_name: string;
  verdict: string | null;
  dcf_value: number | null;
  confidence: string | null;
  current_price: number | null;
  created_at: string;
}

export default function History() {
  const { user, signOut } = useAuth();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from("analysis_history")
      .select("id, ticker, company_name, verdict, dcf_value, confidence, current_price, created_at")
      .order("created_at", { ascending: false })
      .limit(50);

    if (!error && data) setItems(data);
    setLoading(false);
  };

  const verdictColor = (v: string | null) => {
    if (v === "Undervalued") return "text-verdict-under";
    if (v === "Fairly Valued") return "text-verdict-fair";
    if (v === "Overvalued") return "text-verdict-over";
    return "text-muted-foreground";
  };

  return (
    <div className="min-h-screen bg-paper">
      <nav className="sticky top-0 z-50 bg-paper/90 backdrop-blur border-b border-foreground/10">
        <div className="flex items-center justify-between px-6 py-3">
          <Link to="/app" className="flex items-center gap-2.5">
            <span className="inline-block h-5 w-5 bg-ink relative"><span className="absolute inset-[3px] bg-gold" /></span>
            <span className="font-serif-display text-lg tracking-tight text-ink">equimind<span className="text-gold">.</span></span>
          </Link>
          <div className="flex items-center gap-6 font-mono text-[10px] uppercase tracking-[0.25em] text-foreground/70">
            <Link to="/app" className="hover:text-ink">Dashboard</Link>
            <Link to="/app/history" className="text-ink">History</Link>
            <span className="text-foreground/30">|</span>
            <span className="text-foreground/50">{user?.email}</span>
            <button onClick={signOut} className="hover:text-ink">Sign out</button>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4">Research history</div>
        <h1 className="font-serif-display text-5xl tracking-tight text-ink leading-[0.95] mb-4">Past analyses</h1>
        <p className="text-foreground/60 text-sm mb-12">Click any analysis to reopen it with full details.</p>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block h-3 w-3 rounded-full bg-gold pulse-dot" />
            <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">Loading history...</p>
          </div>
        )}

        {!loading && items.length === 0 && (
          <div className="border border-foreground/10 p-12 text-center">
            <p className="font-serif-display text-2xl text-ink mb-2">No analyses yet</p>
            <p className="text-sm text-foreground/50 mb-6">Run your first analysis to see it here.</p>
            <Link to="/app" className="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-paper font-mono text-xs uppercase tracking-[0.3em] hover:bg-gold hover:text-ink transition-colors">New analysis →</Link>
          </div>
        )}

        {!loading && items.length > 0 && (
          <div className="space-y-3">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => navigate(`/app?load=${item.id}`)}
                className="w-full text-left flex items-center justify-between p-5 border border-foreground/10 hover:border-gold/40 hover:shadow-[0_0_0_1px_hsl(var(--gold)/0.15)] transition-all bg-paper group"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-serif-display text-xl text-ink">{item.company_name || item.ticker}</span>
                    <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground px-2 py-0.5 border border-foreground/10">{item.ticker}</span>
                  </div>
                  <div className="font-mono text-[10px] text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>
                <div className="flex items-center gap-6 text-right">
                  {item.dcf_value && (
                    <div>
                      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">DCF</div>
                      <div className="font-serif-display text-lg text-ink">${item.dcf_value.toFixed(2)}</div>
                    </div>
                  )}
                  {item.current_price && (
                    <div>
                      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Price</div>
                      <div className="font-serif-display text-lg text-ink">${item.current_price.toFixed(2)}</div>
                    </div>
                  )}
                  {item.verdict && (
                    <div>
                      <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Verdict</div>
                      <div className={`font-serif-display text-lg ${verdictColor(item.verdict)}`}>{item.verdict}</div>
                    </div>
                  )}
                  <span className="font-mono text-[10px] text-gold/0 group-hover:text-gold/70 transition-colors">Open →</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
