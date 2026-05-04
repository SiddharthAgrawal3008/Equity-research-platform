import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { runPipeline } from "@/lib/api";
import { PipelineLoader } from "@/components/PipelineLoader";
import { CompanyHeaderCard } from "@/components/cards/CompanyHeaderCard";
import { ValuationCard } from "@/components/cards/ValuationCard";
import { RiskCard } from "@/components/cards/RiskCard";
import { NLPCard } from "@/components/cards/NLPCard";
import { ReportCard } from "@/components/cards/ReportCard";
import { DetailPanel } from "@/components/DetailPanel";
import type { ChatMessage, CardType } from "@/types/chat";
import { createId } from "@/types/chat";

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [ticker, setTicker] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [loading, setLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [activeCard, setActiveCard] = useState<{ type: CardType; data: any } | null>(null);
  const [panelFullscreen, setPanelFullscreen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const addMessage = (msg: Omit<ChatMessage, "id" | "timestamp">) => {
    const newMsg = { ...msg, id: createId(), timestamp: new Date() };
    setMessages((prev) => [...prev, newMsg]);
    scrollToBottom();
    return newMsg;
  };

  const handleDownloadPDF = () => {
    const pdfBase64 = pipelineResult?.report?.pdf_base64;
    if (!pdfBase64) return;
    const link = document.createElement("a");
    link.href = `data:application/pdf;base64,${pdfBase64}`;
    const ticker = pipelineResult?.financial_data?.meta?.ticker || "report";
    link.download = `equimind-${ticker}-research-report.pdf`;
    link.click();
  };

  const handleAnalyze = async () => {
    const t = ticker.trim().toUpperCase();
    if (!t || loading) return;

    setActiveCard(null);
    setPipelineResult(null);
    setPanelFullscreen(false);
    setMessages([]);
    setTicker("");
    setLoading(true);

    addMessage({ role: "user", content: `Analyze ${t}` });
    addMessage({ role: "system", content: "Starting pipeline — 5 engines dispatched..." });

    try {
      const result = await runPipeline({
        ticker: t,
        user_id: user?.id,
        session_id: createId(),
      });

      setPipelineResult(result);

      setMessages((prev) => prev.filter((m) => m.role !== "system" || !m.content?.includes("Starting pipeline")));

      if (result.financial_data?.meta?.ticker) {
        addMessage({
          role: "assistant",
          content: `Here's what I found for ${result.financial_data.meta.company_name || t}.`,
          card: { type: "company-header", data: result.financial_data, engineStatus: result.status?.engine_1 },
        });
      }

      if (result.status?.engine_2 === "success") {
        addMessage({
          role: "assistant",
          content: `Valuation complete — ${result.valuation?.summary?.verdict || "analysis ready"}.`,
          card: { type: "valuation", data: result.valuation, engineStatus: "success" },
        });
      } else {
        addMessage({ role: "assistant", content: "Valuation engine encountered an issue. Partial results may be available." });
      }

      if (result.status?.engine_3 === "success") {
        addMessage({
          role: "assistant",
          card: { type: "risk", data: result.risk_metrics, engineStatus: "success" },
        });
      }

      if (result.status?.engine_4 === "success") {
        addMessage({
          role: "assistant",
          card: { type: "nlp", data: result.nlp_insights, engineStatus: "success" },
        });
      }

      if (result.status?.engine_5 === "success") {
        addMessage({
          role: "assistant",
          content: "Research memo ready. Click to read the full report.",
          card: { type: "report", data: result.report, engineStatus: "success" },
        });
      }

      const errors = result.errors || [];
      if (errors.length > 0) {
        addMessage({
          role: "system",
          content: `${errors.length} engine(s) reported issues: ${errors.map((e: any) => e.engine).join(", ")}`,
        });
      }

      addMessage({
        role: "assistant",
        content: "Analysis complete. Click any card to expand details, or ask me a follow-up question.",
      });

    } catch (err: any) {
      addMessage({ role: "system", content: `Pipeline error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = () => {
    const q = followUp.trim();
    if (!q) return;
    setFollowUp("");
    addMessage({ role: "user", content: q });
    addMessage({
      role: "assistant",
      content: "Follow-up Q&A will be powered by Grok — coming in the next build phase. For now, explore the data by clicking the cards above.",
    });
  };

  const panelOpen = activeCard !== null;

  return (
    <div className="h-screen flex flex-col bg-paper">
      {/* Nav */}
      <nav className="flex-none bg-paper/90 backdrop-blur border-b border-foreground/10 z-50">
        <div className="flex items-center justify-between px-6 py-3">
          <Link to="/app" className="flex items-center gap-2.5">
            <span className="inline-block h-5 w-5 bg-ink relative">
              <span className="absolute inset-[3px] bg-gold" />
            </span>
            <span className="font-serif-display text-lg tracking-tight text-ink">
              equimind<span className="text-gold">.</span>
            </span>
          </Link>
          <div className="flex items-center gap-6 font-mono text-[10px] uppercase tracking-[0.25em] text-foreground/70">
            <Link to="/app" className="text-ink">Dashboard</Link>
            <Link to="/app/history" className="hover:text-ink">History</Link>
            <span className="text-foreground/30">|</span>
            <span className="text-foreground/50">{user?.email}</span>
            <button onClick={signOut} className="hover:text-ink">Sign out</button>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT — Chat feed (full width when panel closed) */}
        <div className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${panelOpen && !panelFullscreen ? "border-r border-foreground/10" : ""}`}
          style={{ display: panelFullscreen ? "none" : undefined }}
        >
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {messages.length === 0 && !loading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md">
                  <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4">
                    Research platform
                  </div>
                  <h1 className="font-serif-display text-4xl tracking-tight text-ink leading-[0.95] mb-3">
                    What would you like to analyze?
                  </h1>
                  <p className="text-foreground/50 text-sm mb-8">
                    Enter a ticker symbol below to run the full 5-engine analysis pipeline.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2">
                    {["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN"].map((t) => (
                      <button
                        key={t}
                        onClick={() => setTicker(t)}
                        className="px-3 py-1.5 border border-foreground/15 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:border-gold hover:text-gold transition-colors"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className="mb-4">
                {msg.role === "user" && (
                  <div className="flex justify-end mb-1">
                    <div className="bg-ink text-paper px-4 py-2.5 max-w-sm font-mono text-sm">
                      {msg.content}
                    </div>
                  </div>
                )}

                {msg.role === "system" && (
                  <div className="flex justify-center mb-1">
                    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground px-4 py-2">
                      {msg.content}
                    </div>
                  </div>
                )}

                {msg.role === "assistant" && (
                  <div className="mb-1">
                    {msg.content && (
                      <p className="text-sm text-foreground/70 mb-2 max-w-lg">{msg.content}</p>
                    )}
                    {msg.card && (
                      <div className="max-w-2xl">
                        {msg.card.type === "company-header" && (
                          <CompanyHeaderCard
                            data={msg.card.data}
                            onClick={() => setActiveCard({ type: "company-header", data: msg.card!.data })}
                            active={activeCard?.type === "company-header"}
                          />
                        )}
                        {msg.card.type === "valuation" && (
                          <ValuationCard
                            data={msg.card.data}
                            onClick={() => setActiveCard({ type: "valuation", data: msg.card!.data })}
                            active={activeCard?.type === "valuation"}
                          />
                        )}
                        {msg.card.type === "risk" && (
                          <RiskCard
                            data={msg.card.data}
                            onClick={() => setActiveCard({ type: "risk", data: msg.card!.data })}
                            active={activeCard?.type === "risk"}
                          />
                        )}
                        {msg.card.type === "nlp" && (
                          <NLPCard
                            data={msg.card.data}
                            onClick={() => setActiveCard({ type: "nlp", data: msg.card!.data })}
                            active={activeCard?.type === "nlp"}
                          />
                        )}
                        {msg.card.type === "report" && (
                          <ReportCard
                            data={msg.card.data}
                            onClick={() => setActiveCard({ type: "report", data: msg.card!.data })}
                            active={activeCard?.type === "report"}
                          />
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="max-w-2xl mb-4">
                <PipelineLoader />
              </div>
            )}

            {/* PDF Download button — appears after results */}
            {pipelineResult?.report?.pdf_base64 && !loading && (
              <div className="max-w-2xl mb-4">
                <button
                  onClick={handleDownloadPDF}
                  className="w-full flex items-center justify-between p-4 bg-ink text-paper hover:bg-ink/90 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <span className="inline-flex h-8 w-8 items-center justify-center bg-gold text-ink font-mono text-xs font-bold">
                      PDF
                    </span>
                    <div className="text-left">
                      <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-paper/60">
                        Research memo · {pipelineResult?.financial_data?.meta?.ticker}
                      </div>
                      <div className="text-sm text-paper mt-0.5">
                        Download full equity research report
                      </div>
                    </div>
                  </div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-gold group-hover:translate-x-1 transition-transform">
                    Download ↓
                  </span>
                </button>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          <div className="flex-none border-t border-foreground/10 bg-paper p-4">
            {!pipelineResult ? (
              <div className="flex items-center gap-3 bg-terminal rounded-sm overflow-hidden border border-terminal-line">
                <span className="pl-4 font-serif-display text-xl text-gold/60">$</span>
                <input
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase().slice(0, 6))}
                  onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                  disabled={loading}
                  className="flex-1 bg-transparent outline-none border-0 font-serif-display text-xl text-terminal-foreground py-3 placeholder:text-terminal-dim/40"
                  placeholder="Enter ticker (e.g. AAPL)"
                />
                <button
                  onClick={handleAnalyze}
                  disabled={loading || !ticker.trim()}
                  className="px-6 py-3 bg-ink text-paper font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-gold hover:text-ink disabled:opacity-30 transition-colors"
                >
                  {loading ? "Running..." : "Analyze →"}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3 border border-foreground/15 rounded-sm overflow-hidden">
                <input
                  value={followUp}
                  onChange={(e) => setFollowUp(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleFollowUp()}
                  className="flex-1 bg-transparent outline-none border-0 px-4 py-3 text-sm text-ink placeholder:text-foreground/30"
                  placeholder="Ask a follow-up question about this analysis..."
                />
                <button
                  onClick={handleFollowUp}
                  disabled={!followUp.trim()}
                  className="px-6 py-3 bg-ink text-paper font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-gold hover:text-ink disabled:opacity-30 transition-colors"
                >
                  Ask →
                </button>
              </div>
            )}
            {pipelineResult && (
              <button
                onClick={() => {
                  setPipelineResult(null);
                  setMessages([]);
                  setActiveCard(null);
                  setPanelFullscreen(false);
                }}
                className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:text-ink transition-colors"
              >
                ← New analysis
              </button>
            )}
          </div>
        </div>

        {/* RIGHT — Detail panel (only visible when a card is clicked) */}
        {panelOpen && (
          <div
            className={`flex-none bg-bone/50 overflow-hidden transition-all duration-300 ${
              panelFullscreen ? "w-full" : "w-[520px]"
            }`}
          >
            <DetailPanel
              type={activeCard?.type || null}
              data={activeCard?.data || null}
              fullContext={pipelineResult}
              onClose={() => { setActiveCard(null); setPanelFullscreen(false); }}
              fullscreen={panelFullscreen}
              onToggleFullscreen={() => setPanelFullscreen((f) => !f)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
