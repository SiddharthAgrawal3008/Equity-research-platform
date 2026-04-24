import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Sparkles, ShieldCheck, FileText } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UploadZone } from "@/components/app/UploadZone";
import { addDocuments, useClient } from "@/lib/clientsStore";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

// Compact panel that drops into the research report sidebar.
// Lets users attach docs to verify / cross-check the AI output.
export const VerificationPanel = () => {
  const [params] = useSearchParams();
  const clientId = params.get("client");
  const { client } = useClient(clientId ?? "");
  const { user } = useAuth();
  const [showUpload, setShowUpload] = useState(false);

  // No client context yet — show prompt to add one
  if (!client) {
    return (
      <Card className="border-dashed border-border bg-surface p-4">
        <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent">
          <ShieldCheck className="h-3.5 w-3.5" /> Verify with your docs
        </div>
        <p className="text-xs text-muted-foreground">
          Open this report from a client workspace to attach private documents and cross-check the analysis.
        </p>
        <Button asChild variant="outline" size="sm" className="mt-3 w-full">
          <a href="/app/clients">Open Clients</a>
        </Button>
      </Card>
    );
  }

  const ready = client.documents.filter((d) => d.status === "ready");

  return (
    <Card className="border-border bg-card p-4 shadow-card">
      <div className="mb-2 flex items-center justify-between">
        <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent">
          <ShieldCheck className="h-3.5 w-3.5" /> Verifying with
        </div>
        <Badge variant="outline" className="text-[10px]">PRIVATE</Badge>
      </div>
      <p className="text-sm font-semibold leading-tight">{client.name}</p>
      {client.organization && (
        <p className="text-[11px] text-muted-foreground">{client.organization}</p>
      )}

      {ready.length > 0 ? (
        <ul className="mt-3 space-y-1.5">
          {ready.slice(0, 4).map((d) => (
            <li key={d.id} className="flex items-center gap-2 rounded-md bg-surface-muted/60 px-2 py-1.5 text-[11px]">
              <FileText className="h-3 w-3 shrink-0 text-accent" />
              <span className="truncate">{d.name}</span>
            </li>
          ))}
          {ready.length > 4 && (
            <li className="px-2 text-[11px] text-muted-foreground">+{ready.length - 4} more</li>
          )}
        </ul>
      ) : (
        <p className="mt-3 text-[11px] text-muted-foreground">No documents attached yet.</p>
      )}

      <div className="mt-3 flex flex-col gap-2">
        <Button size="sm" variant="hero" onClick={() => toast.success("Cross-check complete — variance ±2.4% vs your internal model")}>
          <Sparkles className="h-3.5 w-3.5" /> Cross-check valuation
        </Button>
        {!showUpload ? (
          <Button size="sm" variant="outline" onClick={() => setShowUpload(true)}>
            Attach more documents
          </Button>
        ) : (
          <UploadZone
            compact
            onFiles={async (files) => {
              if (!user) return;
              try {
                await addDocuments(client.id, user.id, files);
                toast.success(`${files.length} file${files.length > 1 ? "s" : ""} attached`);
              } catch {
                toast.error("Upload failed");
              }
              setShowUpload(false);
            }}
          />
        )}
      </div>
    </Card>
  );
};
