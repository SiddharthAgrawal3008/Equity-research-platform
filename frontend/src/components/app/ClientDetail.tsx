import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FileText, Sparkles, Trash2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { addDocuments, addReport, deleteClient, useClient } from "@/lib/clientsStore";
import { UploadZone } from "@/components/app/UploadZone";
import { DocumentList } from "@/components/app/DocumentList";
import { TICKERS } from "@/lib/mockData";
import { toast } from "sonner";

export const ClientDetail = () => {
  const { id = "" } = useParams();
  const client = useClient(id);
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);
  const [ticker, setTicker] = useState("");

  if (!client) {
    return (
      <div className="container py-16 text-center">
        <p className="text-muted-foreground">Client not found.</p>
        <Button asChild variant="hero" className="mt-4">
          <Link to="/app/clients"><ArrowLeft className="h-4 w-4" /> Back to clients</Link>
        </Button>
      </div>
    );
  }

  const toggle = (docId: string) =>
    setSelected((s) => (s.includes(docId) ? s.filter((x) => x !== docId) : [...s, docId]));

  const onUpload = (files: File[]) => {
    addDocuments(client.id, files);
    toast.success(`${files.length} file${files.length > 1 ? "s" : ""} uploading…`);
  };

  const generate = (tk: string | null) => {
    const sourceIds = selected.length > 0 ? selected : client.documents.filter((d) => d.status === "ready").map((d) => d.id);
    if (sourceIds.length === 0) {
      toast.error("Upload at least one document first");
      return;
    }
    if (tk) {
      addReport(client.id, {
        ticker: tk.toUpperCase(),
        title: `${tk.toUpperCase()} — Verified with client docs`,
        rating: "BUY",
        intrinsic: 198.4,
        upside: 12.2,
        sourceDocIds: sourceIds,
      });
      navigate(`/app/research/${tk.toUpperCase()}?client=${client.id}&docs=${sourceIds.join(",")}`);
    } else {
      navigate(`/app/analyze?client=${client.id}&docs=${sourceIds.join(",")}`);
    }
  };

  const readyDocs = client.documents.filter((d) => d.status === "ready").length;

  return (
    <div className="container py-6 lg:py-8">
      <div className="mb-4">
        <Button asChild variant="ghost" size="sm">
          <Link to="/app/clients"><ArrowLeft className="h-4 w-4" /> All clients</Link>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          {/* Client header */}
          <Card className="border-border bg-card p-6 shadow-card">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-navy font-display text-lg font-semibold text-primary-foreground">
                  {client.name.charAt(0)}
                </div>
                <div>
                  <h1 className="font-display text-2xl font-semibold tracking-tight">{client.name}</h1>
                  {client.organization && (
                    <p className="text-sm text-muted-foreground">{client.organization}</p>
                  )}
                </div>
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-bear">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete this client?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will remove {client.documents.length} documents and {client.reports.length} reports. This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => {
                        deleteClient(client.id);
                        toast.success("Client deleted");
                        navigate("/app/clients");
                      }}
                      className="bg-bear text-bear-foreground hover:bg-bear/90"
                    >
                      Delete client
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
            {client.notes && (
              <p className="mt-4 rounded-md border border-border bg-surface-muted p-3 text-sm text-muted-foreground">
                {client.notes}
              </p>
            )}
          </Card>

          {/* Upload */}
          <section>
            <h2 className="mb-3 text-sm font-semibold">Documents</h2>
            <UploadZone onFiles={onUpload} />
            <div className="mt-4">
              <DocumentList
                clientId={client.id}
                documents={client.documents}
                selectable
                selectedIds={selected}
                onToggleSelect={toggle}
                empty="Drop in 10-Ks, earnings transcripts, internal models or any supporting docs."
              />
            </div>
          </section>

          {/* Reports */}
          <section>
            <h2 className="mb-3 text-sm font-semibold">Research history</h2>
            {client.reports.length === 0 ? (
              <Card className="border-dashed border-border bg-surface-muted/40 p-8 text-center text-sm text-muted-foreground">
                No reports generated yet for this client.
              </Card>
            ) : (
              <ul className="space-y-2">
                {client.reports.map((r) => (
                  <li key={r.id}>
                    <Link
                      to={r.ticker ? `/app/research/${r.ticker}?client=${client.id}` : `/app/analyze?report=${r.id}&client=${client.id}`}
                      className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-all hover:border-accent/50 hover:shadow-card"
                    >
                      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent-soft text-accent">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold">{r.title}</span>
                          <Badge
                            className={
                              r.rating === "BUY"
                                ? "bg-bull text-bull-foreground hover:bg-bull"
                                : r.rating === "SELL"
                                ? "bg-bear text-bear-foreground hover:bg-bear"
                                : "bg-neutral text-neutral-foreground hover:bg-neutral"
                            }
                          >
                            {r.rating}
                          </Badge>
                        </div>
                        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{new Date(r.createdAt).toLocaleDateString()}</span>
                          <span>·</span>
                          <span>{r.sourceDocIds.length} sources</span>
                          {r.intrinsic != null && (
                            <>
                              <span>·</span>
                              <span className="font-mono-num">IV ${r.intrinsic.toFixed(2)}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        {/* Sticky generate panel */}
        <aside>
          <Card className="border-border bg-card p-5 shadow-card lg:sticky lg:top-20">
            <div className="mb-3 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent">
              <Sparkles className="h-3.5 w-3.5" /> Generate analysis
            </div>
            <p className="text-xs text-muted-foreground">
              {selected.length > 0
                ? `Using ${selected.length} selected document${selected.length > 1 ? "s" : ""}.`
                : `Will use all ${readyDocs} ready document${readyDocs === 1 ? "" : "s"}.`}
            </p>

            <div className="mt-5 space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Verify against ticker (optional)</label>
              <div className="flex gap-2">
                <Input
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="AAPL"
                  className="font-mono-num"
                />
                <Button variant="hero" onClick={() => generate(ticker || null)} disabled={!ticker.trim()}>
                  Verify
                </Button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {TICKERS.slice(0, 5).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTicker(t)}
                    className="rounded-full border border-border bg-surface px-2 py-0.5 font-mono-num text-[11px] hover:border-accent hover:text-accent"
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="my-5 flex items-center gap-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
            </div>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => generate(null)}
              disabled={readyDocs === 0}
            >
              Analyze from documents only
            </Button>
            <p className="mt-2 text-[11px] text-muted-foreground">
              Generate a research memo using only the uploaded files — no public ticker required.
            </p>
          </Card>
        </aside>
      </div>
    </div>
  );
};
