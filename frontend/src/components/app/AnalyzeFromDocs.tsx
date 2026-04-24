import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, Sparkles, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UploadZone } from "@/components/app/UploadZone";
import { addDocuments, useClient } from "@/lib/clientsStore";
import { useAuth } from "@/context/AuthContext";
import { motion } from "framer-motion";
import { toast } from "sonner";

const STAGES = [
  "Indexing uploaded documents",
  "Extracting financial tables",
  "Running valuation cross-check",
  "Scoring sentiment & risk",
  "Drafting investment memo",
];

export const AnalyzeFromDocs = () => {
  const [params] = useSearchParams();
  const clientId = params.get("client") ?? "";
  const docIds = (params.get("docs") ?? "").split(",").filter(Boolean);
  const { client, loading } = useClient(clientId);
  const { user } = useAuth();

  const [stage, setStage] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (stage >= STAGES.length) {
      setDone(true);
      return;
    }
    const t = setTimeout(() => setStage((s) => s + 1), 700);
    return () => clearTimeout(t);
  }, [stage]);

  const sourceDocs = useMemo(
    () => client?.documents.filter((d) => docIds.includes(d.id)) ?? [],
    [client, docIds],
  );

  if (loading) {
    return (
      <div className="container flex items-center justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="container py-16 text-center text-sm text-muted-foreground">
        No client context. <Link to="/app/clients" className="text-accent">Go to clients</Link>.
      </div>
    );
  }

  return (
    <div className="container py-6 lg:py-8">
      <div className="mb-4">
        <Button asChild variant="ghost" size="sm">
          <Link to={`/app/clients/${client.id}`}><ArrowLeft className="h-4 w-4" /> Back to {client.name}</Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <Card className="border-border bg-card p-6 shadow-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent">EquiMind Research Note</div>
            <h1 className="mt-2 font-display text-2xl font-semibold tracking-tight">
              Private analysis · {client.name}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Generated from {sourceDocs.length} client document{sourceDocs.length === 1 ? "" : "s"} · no public ticker.
            </p>
          </Card>

          {!done ? (
            <Card className="border-border bg-card p-8 shadow-card">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-accent" />
                <span className="text-sm font-semibold">Synthesising memo from your documents...</span>
              </div>
              <ul className="mt-6 space-y-3">
                {STAGES.map((s, i) => (
                  <motion.li
                    key={s}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-3 text-sm"
                  >
                    {i < stage ? (
                      <CheckCircle2 className="h-4 w-4 text-bull" />
                    ) : i === stage ? (
                      <Loader2 className="h-4 w-4 animate-spin text-accent" />
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-muted" />
                    )}
                    <span className={i < stage ? "text-muted-foreground line-through" : i === stage ? "text-foreground" : "text-muted-foreground/60"}>
                      {s}
                    </span>
                  </motion.li>
                ))}
              </ul>
            </Card>
          ) : (
            <Card className="border-border bg-card p-10 shadow-card text-center">
              <Sparkles className="mx-auto h-8 w-8 text-accent mb-4" />
              <h2 className="font-display text-xl font-semibold">Document-only analysis coming soon</h2>
              <p className="mt-3 text-sm text-muted-foreground max-w-sm mx-auto">
                For now, use the ticker verification path on the client page to generate a full research report cross-referenced with your uploaded documents.
              </p>
              <Button asChild variant="hero" className="mt-6">
                <Link to={`/app/clients/${client.id}`}>Back to {client.name}</Link>
              </Button>
            </Card>
          )}
        </div>

        <aside>
          <Card className="border-border bg-card p-5 shadow-card lg:sticky lg:top-20">
            <div className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent">
              <Sparkles className="h-3.5 w-3.5" /> Source documents
            </div>
            {sourceDocs.length === 0 ? (
              <>
                <p className="mb-3 text-xs text-muted-foreground">
                  No source docs selected. Drop in additional supporting material:
                </p>
                <UploadZone compact onFiles={async (files) => {
                  if (!user) return;
                  try {
                    await addDocuments(client.id, user.id, files);
                    toast.success(`${files.length} file${files.length > 1 ? "s" : ""} added to ${client.name}`);
                  } catch {
                    toast.error("Upload failed");
                  }
                }} />
              </>
            ) : (
              <ul className="space-y-2">
                {sourceDocs.map((d) => (
                  <li key={d.id} className="flex items-center gap-2 rounded-md border border-border bg-surface-muted/50 px-3 py-2 text-xs">
                    <FileText className="h-3.5 w-3.5 shrink-0 text-accent" />
                    <span className="truncate flex-1">{d.name}</span>
                    <Badge variant="outline" className="text-[9px]">{d.kind.toUpperCase()}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </aside>
      </div>
    </div>
  );
};
