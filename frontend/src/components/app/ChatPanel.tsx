import { useEffect, useRef, useState } from "react";
import { Loader2, Search, SendHorizontal, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ResearchReport } from "@/components/research/ResearchReport";
import { useAuth } from "@/context/AuthContext";
import { useMessages } from "@/hooks/useMessages";
import { addMessage as dbAddMessage, saveResearchResult, type Message, type Session } from "@/lib/db";
import { fetchResearch, pingBackend, BASE_URL } from "@/lib/api";
import type { CompanyData } from "@/lib/mockData";

interface ChatPanelProps {
  activeSession: Session | null;
  onSessionCreate: (title: string) => Promise<Session>;
}

export function ChatPanel({ activeSession, onSessionCreate }: ChatPanelProps) {
  const { user } = useAuth();
  const { messages, loading } = useMessages(activeSession?.id ?? null);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [pendingTicker, setPendingTicker] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "error">("checking");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, pending]);

  useEffect(() => {
    pingBackend().then((ok) => setBackendStatus(ok ? "ok" : "error"));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ticker = input.trim().toUpperCase();
    if (!ticker || pending || !user) return;
    setInput("");
    setPending(true);
    setPendingTicker(ticker);

    try {
      let sessionId = activeSession?.id ?? null;
      if (!sessionId) {
        const newSession = await onSessionCreate(ticker);
        sessionId = newSession.id;
      }

      await dbAddMessage(sessionId, user.id, "user", ticker, "text");

      let data: CompanyData;
      try {
        data = await fetchResearch(ticker);
      } catch (err) {
        await dbAddMessage(sessionId, user.id, "assistant", String(err), "error");
        return;
      }

      await dbAddMessage(sessionId, user.id, "assistant", JSON.stringify(data), "research", { ticker });
      await saveResearchResult(sessionId, user.id, ticker, data);
    } finally {
      setPending(false);
      setPendingTicker(null);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : messages.length === 0 && !pending ? (
          <EmptyState backendStatus={backendStatus} backendUrl={BASE_URL} />
        ) : (
          <div className="space-y-6 px-4 py-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {pending && pendingTicker && <PendingBubble ticker={pendingTicker} />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-border p-4">
        <div className="mx-auto flex max-w-3xl gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter a ticker (e.g. AAPL, TSLA)…"
            disabled={pending}
            className="flex-1"
          />
          <Button type="submit" disabled={!input.trim() || pending} size="icon">
            {pending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <SendHorizontal className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}

function EmptyState({
  backendStatus,
  backendUrl,
}: {
  backendStatus: "checking" | "ok" | "error";
  backendUrl: string;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-4 text-center">
      <div className="rounded-full border border-border p-4">
        <Search className="h-8 w-8 text-muted-foreground" />
      </div>
      <div>
        <h2 className="font-display text-xl font-semibold">Analyze any stock</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter a ticker symbol below to get a full research report
        </p>
      </div>

      {/* Backend status pill */}
      <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs">
        {backendStatus === "checking" && (
          <>
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
            <span className="text-muted-foreground">Checking backend…</span>
          </>
        )}
        {backendStatus === "ok" && (
          <>
            <Wifi className="h-3 w-3 text-bull" />
            <span className="text-bull font-medium">Backend connected</span>
          </>
        )}
        {backendStatus === "error" && (
          <>
            <WifiOff className="h-3 w-3 text-bear" />
            <span className="text-bear font-medium">Backend unreachable</span>
            <span className="text-muted-foreground">·</span>
            <code className="max-w-[180px] truncate font-mono text-[10px] text-muted-foreground">
              {backendUrl}
            </code>
          </>
        )}
      </div>

      {backendStatus === "error" && (
        <p className="max-w-sm text-xs text-muted-foreground">
          The backend is not responding at the configured URL. Check that{" "}
          <code className="rounded bg-surface px-1 py-0.5 font-mono text-[11px]">VITE_API_BASE_URL</code>{" "}
          is set correctly in Vercel and the backend server is running.
        </p>
      )}
    </div>
  );
}

function PendingBubble({ ticker }: { ticker: string }) {
  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <div className="rounded-2xl bg-primary px-4 py-2 text-sm text-primary-foreground">
          {ticker}
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Analyzing {ticker} — this may take up to 2 minutes…
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl bg-primary px-4 py-2 text-sm text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.type === "error") {
    return (
      <div className="rounded-xl border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {message.content}
      </div>
    );
  }

  if (message.type === "research") {
    let data: CompanyData | null = null;
    try {
      data = JSON.parse(message.content) as CompanyData;
    } catch {
      return (
        <div className="rounded-xl border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          Failed to parse research data.
        </div>
      );
    }
    const ticker = (message.metadata?.ticker as string) ?? data.ticker;
    return (
      <div className="overflow-hidden rounded-xl border border-border bg-background">
        <ResearchReport ticker={ticker} data={data} />
      </div>
    );
  }

  return (
    <div className="max-w-[80%] rounded-2xl bg-secondary px-4 py-2 text-sm text-secondary-foreground">
      {message.content}
    </div>
  );
}
