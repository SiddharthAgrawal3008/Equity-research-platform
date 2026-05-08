import { useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { runPipeline, sendChat } from "@/lib/api";
import { supabase } from "@/lib/supabase";
import { PipelineLoader } from "@/components/PipelineLoader";
import { CompanyHeaderCard } from "@/components/cards/CompanyHeaderCard";
import { ValuationCard } from "@/components/cards/ValuationCard";
import { RiskCard } from "@/components/cards/RiskCard";
import { NLPCard } from "@/components/cards/NLPCard";
import { ReportCard } from "@/components/cards/ReportCard";
import { DetailPanel } from "@/components/DetailPanel";
import type { ChatMessage, CardType } from "@/types/chat";
import { createId } from "@/types/chat";
import ReactMarkdown from "react-markdown";

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [ticker, setTicker] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const [activeCard, setActiveCard] = useState<{ type: CardType; data: any } | null>(null);
  const [panelFullscreen, setPanelFullscreen] = useState(false);
  const [loadedHistoryId, setLoadedHistoryId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [searchParams] = useSearchParams();

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const addMsg = (msg: Omit<ChatMessage, "id" | "timestamp">) => {
    const m = { ...msg, id: createId(), timestamp: new Date() };
    setMessages((p) => [...p, m]);
    scrollToBottom();
  };

  const populateFromResult = (result: any) => {
    setPipelineResult(result);
    const msgs: Omit<ChatMessage, "id" | "timestamp">[] = [];
    const name = result.financial_data?.meta?.company_name || result.financial_data?.meta?.ticker || "Unknown";

    if (result.financial_data?.meta?.ticker) {
      msgs.push({ role: "assistant", content: `Here's the analysis for ${name}.`, card: { type: "company-header", data: result.financial_data, engineStatus: "success" } });
    }
    if (result.status?.engine_2 === "success" || result.valuation?.dcf?.status === "success") {
      msgs.push({ role: "assistant", content: `Valuation: ${result.valuation?.summary?.verdict || "ready"}.`, card: { type: "valuation", data: result.valuation, engineStatus: "success" } });
    }
    if (result.status?.engine_3 === "success" || result.risk_metrics?.market_risk) {
      msgs.push({ role: "assistant", card: { type: "risk", data: result.risk_metrics, engineStatus: "success" } });
    }
    if (result.status?.engine_4 === "success" || result.nlp_insights?.sentiment) {
      msgs.push({ role: "assistant", card: { type: "nlp", data: result.nlp_insights, engineStatus: "success" } });
    }
    if (result.status?.engine_5 === "success" || result.report?.sections) {
      msgs.push({ role: "assistant", content: "Research memo ready.", card: { type: "report", data: result.report, engineStatus: "success" } });
    }
    msgs.push({ role: "assistant", content: "Click any card to expand details, or ask a follow-up question." });

    setMessages(msgs.map((m) => ({ ...m, id: createId(), timestamp: new Date() })));
    scrollToBottom();
  };

  const historyIdParam = searchParams.get("load");
  if (historyIdParam && historyIdParam !== loadedHistoryId) {
    setLoadedHistoryId(historyIdParam);
    supabase.from("analysis_history").select("result_json").eq("id", historyIdParam).single().then(({ data }) => {
      if (data?.result_json) {
        setActiveCard(null);
        setPanelFullscreen(false);
        populateFromResult(data.result_json);
      }
    });
  }

  const handleDownloadPDF = () => {
    const b64 = pipelineResult?.report?.pdf_base64;
    if (!b64) return;
    const a = document.createElement("a");
    a.href = `data:application/pdf;base64,${b64}`;
    a.download = `equimind-${pipelineResult?.financial_data?.meta?.ticker || "report"}-research.pdf`;
    a.click();
  };

  const handleAnalyze = async () => {
    const t = ticker.trim().toUpperCase();
    if (!t || loading) return;
    setActiveCard(null); setPipelineResult(null); setPanelFullscreen(false); setMessages([]); setTicker(""); setLoading(true);

    addMsg({ role: "user", content: `Analyze ${t}` });
    addMsg({ role: "system", content: "Starting pipeline — 5 engines dispatched..." });

    try {
      const result = await runPipeline({ ticker: t, user_id: user?.id, session_id: createId() });

      if (user?.id) {
        supabase.from("analysis_history").insert({
          user_id: user.id, ticker: t,
          company_name: result.financial_data?.meta?.company_name || t,
          verdict: result.valuation?.summary?.verdict || null,
          dcf_value: result.valuation?.dcf?.intrinsic_value_per_share || null,
          confidence: result.valuation?.summary?.confidence || null,
          current_price: result.financial_data?.meta?.current_price || null,
          result_json: result,
        }).then(() => {});
      }

      setMessages([]);
      populateFromResult(result);

    } catch (err: any) {
      addMsg({ role: "system", content: `Pipeline error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = async () => {
    const q = followUp.trim();
    if (!q || chatLoading) return;
    setFollowUp(""); setChatLoading(true);
    addMsg({ role: "user", content: q });

    try {
      const res = await sendChat({ question: q, analysis_context: pipelineResult || {} });
      addMsg({ role: "assistant", content: res.answer });
    } catch (err: any) {
      addMsg({ role: "assistant", content: `Sorry, I couldn't process that: ${err.message}` });
    } finally {
      setChatLoading(false);
    }
  };

  const panelOpen = activeCard !== null;

  return (
    <div className="h-screen flex flex-col bg-paper">
      {/* Nav */}
      <nav className="flex-none bg-paper/90 backdrop-blur border-b border-foreground/10 z-50">
        <div className="flex items-center justify-between px-6 py-3">
          <Link to="/app" className="flex items-center gap-2.5">
            <span className="inline-block h-5 w-5 bg-ink relative"><span className="absolute inset-[3px] bg-gold" /></span>
            <span className="font-serif-display text-lg tracking-tight text-ink">equimind<span className="text-gold">.</span></span>
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
        {/* LEFT — Chat feed */}
        <div className={`flex flex-col min-w-0 transition-all duration-300 ${panelFullscreen ? "hidden" : panelOpen ? "flex-1 border-r border-foreground/10" : "flex-1"}`}>

          {/* Scrollable chat area */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className={`mx-auto ${panelOpen ? "max-w-2xl" : "max-w-3xl"}`}>

              {/* Empty state */}
              {messages.length === 0 && !loading && (
                <div className="flex items-center justify-center" style={{ minHeight: "60vh" }}>
                  <div className="text-center max-w-md">
                    <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-gold mb-4">Research platform</div>
                    <h1 className="font-serif-display text-4xl tracking-tight text-ink leading-[0.95] mb-3">What would you like to analyze?</h1>
                    <p className="text-foreground/50 text-sm mb-8">Enter a ticker symbol below to run the full 5-engine analysis pipeline.</p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN"].map((t) => (
                        <button key={t} onClick={() => setTicker(t)} className="px-3 py-1.5 border border-foreground/15 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:border-gold hover:text-gold transition-colors">{t}</button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Messages */}
              {messages.map((msg) => (
                <div key={msg.id} className="mb-4">
                  {/* User message */}
                  {msg.role === "user" && (
                    <div className="flex justify-end mb-1">
                      <div className="bg-ink text-paper px-4 py-2.5 max-w-sm font-mono text-sm">{msg.content}</div>
                    </div>
                  )}

                  {/* System message */}
                  {msg.role === "system" && (
                    <div className="flex justify-center mb-1">
                      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground px-4 py-2">{msg.content}</div>
                    </div>
                  )}

                  {/* Assistant message */}
                  {msg.role === "assistant" && (
                    <div className="mb-1">
                      {/* Text-only message (follow-up answers) — render markdown */}
                      {msg.content && !msg.card && (
                        <div className="bg-bone/50 border border-foreground/5 px-4 py-3 max-w-xl prose prose-sm prose-stone">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      )}

                      {/* Text + card message — plain text label above card */}
                      {msg.content && msg.card && (
                        <p className="text-sm text-foreground/70 mb-2">{msg.content}</p>
                      )}

                      {/* Engine cards */}
                      {msg.card?.type === "company-header" && <CompanyHeaderCard data={msg.card.data} onClick={() => setActiveCard({ type: "company-header", data: msg.card!.data })} active={activeCard?.type === "company-header"} />}
                      {msg.card?.type === "valuation" && <ValuationCard data={msg.card.data} onClick={() => setActiveCard({ type: "valuation", data: msg.card!.data })} active={activeCard?.type === "valuation"} />}
                      {msg.card?.type === "risk" && <RiskCard data={msg.card.data} onClick={() => setActiveCard({ type: "risk", data: msg.card!.data })} active={activeCard?.type === "risk"} />}
                      {msg.card?.type === "nlp" && <NLPCard data={msg.card.data} onClick={() => setActiveCard({ type: "nlp", data: msg.card!.data })} active={activeCard?.type === "nlp"} />}
                      {msg.card?.type === "report" && <ReportCard data={msg.card.data} onClick={() => setActiveCard({ type: "report", data: msg.card!.data })} active={activeCard?.type === "report"} />}
                    </div>
                  )}
                </div>
              ))}

              {/* Pipeline loading animation */}
              {loading && <div className="mb-4"><PipelineLoader /></div>}

              {/* Chat thinking indicator */}
              {chatLoading && (
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-gold pulse-dot" />
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Thinking...</span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Fixed bottom bar — PDF button + input */}
          <div className="flex-none border-t border-foreground/10 bg-paper px-6 py-4">
            <div className={`mx-auto ${panelOpen ? "max-w-2xl" : "max-w-3xl"}`}>

              {/* PDF download — pinned above input when available */}
              {pipelineResult?.report?.pdf_base64 && (
                <button onClick={handleDownloadPDF} className="w-full flex items-center justify-between p-3 mb-3 bg-ink text-paper hover:bg-ink/90 transition-colors group">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex h-7 w-7 items-center justify-center bg-gold text-ink font-mono text-[10px] font-bold">PDF</span>
                    <div className="text-left">
                      <div className="font-mono text-[9px] uppercase tracking-[0.25em] text-paper/60">Research memo · {pipelineResult?.financial_data?.meta?.ticker}</div>
                      <div className="text-xs text-paper mt-0.5">Download full report</div>
                    </div>
                  </div>
                  <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-gold">Download ↓</span>
                </button>
              )}

              {/* Ticker input OR follow-up input */}
              {!pipelineResult ? (
                <div className="flex items-center gap-3 bg-terminal rounded-sm overflow-hidden border border-terminal-line">
                  <span className="pl-4 font-serif-display text-xl text-gold/60">$</span>
                  <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase().slice(0, 6))} onKeyDown={(e) => e.key === "Enter" && handleAnalyze()} disabled={loading} className="flex-1 bg-transparent outline-none border-0 font-serif-display text-xl text-terminal-foreground py-3 placeholder:text-terminal-dim/40" placeholder="Enter ticker (e.g. AAPL)" />
                  <button onClick={handleAnalyze} disabled={loading || !ticker.trim()} className="px-6 py-3 bg-ink text-paper font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-gold hover:text-ink disabled:opacity-30 transition-colors">{loading ? "Running..." : "Analyze →"}</button>
                </div>
              ) : (
                <div className="flex items-center gap-3 border border-foreground/15 rounded-sm overflow-hidden">
                  <input value={followUp} onChange={(e) => setFollowUp(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleFollowUp()} disabled={chatLoading} className="flex-1 bg-transparent outline-none border-0 px-4 py-3 text-sm text-ink placeholder:text-foreground/30" placeholder="Ask a follow-up question about this analysis..." />
                  <button onClick={handleFollowUp} disabled={!followUp.trim() || chatLoading} className="px-6 py-3 bg-ink text-paper font-mono text-[10px] uppercase tracking-[0.3em] hover:bg-gold hover:text-ink disabled:opacity-30 transition-colors">{chatLoading ? "..." : "Ask →"}</button>
                </div>
              )}

              {/* New analysis button */}
              {pipelineResult && (
                <button onClick={() => { setPipelineResult(null); setMessages([]); setActiveCard(null); setPanelFullscreen(false); setLoadedHistoryId(null); }} className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:text-ink transition-colors">← New analysis</button>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT — Detail panel (only when card is clicked) */}
        {panelOpen && (
          <div className={`flex-none bg-bone/50 overflow-hidden transition-all duration-300 ${panelFullscreen ? "w-full" : "w-[520px]"}`}>
            <DetailPanel type={activeCard?.type || null} data={activeCard?.data || null} fullContext={pipelineResult} onClose={() => { setActiveCard(null); setPanelFullscreen(false); }} fullscreen={panelFullscreen} onToggleFullscreen={() => setPanelFullscreen((f) => !f)} />
          </div>
        )}
      </div>
    </div>
  );
}
