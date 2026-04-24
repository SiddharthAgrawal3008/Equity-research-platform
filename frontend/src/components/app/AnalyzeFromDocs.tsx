import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, Sparkles, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UploadZone } from "@/components/app/UploadZone";
import { DocumentList } from "@/components/app/DocumentList";
import { addDocuments, useClient } from "@/lib/clientsStore";
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
  const client = useClient(clientId);

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
            <GeneratedMemo client={client.name} sources={sourceDocs.length} />
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
                <UploadZone compact onFiles={(files) => {
                  addDocuments(client.id, files);
                  toast.success(`${files.length} file${files.length > 1 ? "s" : ""} added to ${client.name}`);
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

const GeneratedMemo = ({ client, sources }: { client: string; sources: number }) => (
  <Card className="border-border bg-card p-8 shadow-card">
    <div className="border-b border-border pb-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold">Investment Memo · Private</h2>
        <Badge className="bg-bull text-bull-foreground hover:bg-bull">BUY · Conditional</Badge>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">For {client} · synthesised from {sources} source documents</p>
    </div>

    {[
      { n: "1", t: "Business Summary", c: "Subject company operates in the consumer technology space with a recurring services franchise. Documents indicate revenue growth in the high single digits and gross margin expansion driven by mix shift toward services." },
      { n: "2", t: "Financial Performance (extracted)", c: "Revenue ~$391B (TTM, per uploaded 10-K, p.45). Operating margin 31.5%. Free cash flow conversion >100% of net income. Internal DCF model assumes 4.5% revenue CAGR through Year 5." },
      { n: "3", t: "Cross-Check vs Internal Model", c: "EquiMind base-case intrinsic value of $198 is within 3% of your internal model's $193 base case. Sensitivity analysis confirms valuation robustness across WACC range 7.5–9.5%." },
      { n: "4", t: "Key Risks (from documents)", c: "Concentration in greater-China revenue (~17%, per 10-K Item 1A). Regulatory pressure on App Store economics flagged in earnings transcript Q&A. Supply chain commentary remained constructive." },
      { n: "5", t: "Investment Thesis", c: "Documents corroborate the public thesis: services momentum and gross-margin expansion underpin a base-case fair value with ~12% upside. Verification with internal model strengthens conviction." },
      { n: "6", t: "Bear Case", c: "Per management commentary, sustained China softness combined with adverse App Store remedy could compress fair value to ~$158 — consistent with the bear scenario in your internal model." },
    ].map((s) => (
      <section key={s.n} className="mt-5 border-b border-border pb-5 last:border-b-0">
        <div className="mb-1.5 flex items-baseline gap-3">
          <span className="font-mono-num text-xs font-semibold text-accent">{s.n}</span>
          <h3 className="font-display text-base font-semibold">{s.t}</h3>
        </div>
        <p className="text-sm leading-relaxed text-foreground/85">{s.c}</p>
      </section>
    ))}

    <div className="mt-6 flex items-center justify-between border-t border-border pt-4 text-[11px] text-muted-foreground">
      <span>Generated · {new Date().toLocaleDateString()}</span>
      <Badge variant="outline" className="border-border">Private — for client use only</Badge>
    </div>
  </Card>
);
