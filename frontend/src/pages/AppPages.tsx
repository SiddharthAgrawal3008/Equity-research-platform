import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ThemeProvider } from "@/components/app/ThemeProvider";
import { AppTopBar } from "@/components/app/AppTopBar";
import { QueryScreen } from "@/components/app/QueryScreen";
import { LoadingScreen } from "@/components/app/LoadingScreen";
import { ResearchReport } from "@/components/research/ResearchReport";
import { ClientsList } from "@/components/app/ClientsList";
import { ClientDetail } from "@/components/app/ClientDetail";
import { AnalyzeFromDocs } from "@/components/app/AnalyzeFromDocs";
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

export const AppHome = () => withApp(<QueryScreen />);

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
