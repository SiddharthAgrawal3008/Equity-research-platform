import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import { AppTopBar } from "@/components/app/AppTopBar";
import { LoadingScreen } from "@/components/app/LoadingScreen";
import { ResearchReport } from "@/components/research/ResearchReport";
import { ClientsList } from "@/components/app/ClientsList";
import { ClientDetail } from "@/components/app/ClientDetail";
import { AnalyzeFromDocs } from "@/components/app/AnalyzeFromDocs";
import { Sidebar } from "@/components/app/Sidebar";
import { ChatPanel } from "@/components/app/ChatPanel";
import { useSessions } from "@/hooks/useSessions";
import { fetchResearch } from "@/lib/api";
import type { CompanyData } from "@/lib/mockData";

const AppShell = ({ children }: { children: React.ReactNode }) => (
  <div className="flex min-h-screen flex-col bg-background text-foreground">
    <AppTopBar />
    <div className="flex flex-1 flex-col">{children}</div>
  </div>
);

const withApp = (node: React.ReactNode) => (
  <ThemeProvider>
    <AppShell>{node}</AppShell>
  </ThemeProvider>
);

export const AppHome = () => {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const { sessions, loading, createSession } = useSessions();

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  const handleSessionCreate = async (title: string) => {
    const session = await createSession(title);
    setActiveSessionId(session.id);
    return session;
  };

  return (
    <ThemeProvider>
      <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
        <AppTopBar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelect={setActiveSessionId}
            onNew={() => setActiveSessionId(null)}
            loading={loading}
          />
          <ChatPanel
            activeSession={activeSession}
            onSessionCreate={handleSessionCreate}
          />
        </div>
      </div>
    </ThemeProvider>
  );
};

export const AppResearch = () => {
  const { ticker = "" } = useParams();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<CompanyData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setData(null);
    setError(null);
    fetchResearch(ticker)
      .then((result) => setData(result))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [ticker]);

  return withApp(
    loading ? (
      <LoadingScreen ticker={ticker.toUpperCase()} onComplete={() => {}} />
    ) : (
      <ResearchReport ticker={ticker} data={data} fetchError={error} />
    ),
  );
};

export const AppClients = () => withApp(<ClientsList />);
export const AppClientDetail = () => withApp(<ClientDetail />);
export const AppAnalyze = () => withApp(<AnalyzeFromDocs />);
