import { Loader2, CheckCircle2, AlertCircle, MoreVertical, Trash2, Eye } from "lucide-react";
import { UploadedDoc, formatBytes, removeDoc } from "@/lib/clientsStore";
import { DocIcon, docColor } from "@/components/app/DocIcon";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface Props {
  documents: UploadedDoc[];
  selectable?: boolean;
  selectedIds?: string[];
  onToggleSelect?: (id: string) => void;
  empty?: React.ReactNode;
}

export const DocumentList = ({
  documents,
  selectable,
  selectedIds = [],
  onToggleSelect,
  empty,
}: Props) => {
  if (documents.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface-muted/40 p-8 text-center text-sm text-muted-foreground">
        {empty ?? "No documents uploaded yet."}
      </div>
    );
  }

  return (
    <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border bg-surface">
      {documents.map((d) => {
        const checked = selectedIds.includes(d.id);
        return (
          <li
            key={d.id}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-secondary/40"
          >
            {selectable && (
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggleSelect?.(d.id)}
                className="h-4 w-4 cursor-pointer accent-accent"
              />
            )}
            <span
              className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border ${docColor(d.kind)}`}
            >
              <DocIcon kind={d.kind} />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium text-foreground">{d.name}</span>
                <StatusPill status={d.status} />
              </div>
              <div className="mt-0.5 text-xs text-muted-foreground font-mono-num">
                {formatBytes(d.size)}
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => toast.info("Document preview coming soon")}>
                  <Eye className="h-4 w-4" /> Preview parse
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={async () => {
                    try {
                      await removeDoc(d.id, d.storage_path);
                      toast.success("Document removed");
                    } catch {
                      toast.error("Failed to remove document");
                    }
                  }}
                  className="text-bear focus:text-bear"
                >
                  <Trash2 className="h-4 w-4" /> Remove
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </li>
        );
      })}
    </ul>
  );
};

const StatusPill = ({ status }: { status: string }) => {
  if (status === "ready")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-bull/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-bull">
        <CheckCircle2 className="h-3 w-3" /> Ready
      </span>
    );
  if (status === "error")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-bear/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-bear">
        <AlertCircle className="h-3 w-3" /> Error
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-accent">
      <Loader2 className="h-3 w-3 animate-spin" />
      {status === "uploading" ? "Uploading" : "Parsing"}
    </span>
  );
};
