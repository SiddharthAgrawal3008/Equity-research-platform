import { MessageSquare, PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { Session } from "@/lib/db";

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  loading?: boolean;
}

export function Sidebar({ sessions, activeSessionId, onSelect, onNew, loading }: SidebarProps) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-card">
      <div className="p-3">
        <Button variant="outline" className="w-full justify-start gap-2" onClick={onNew}>
          <PlusIcon className="h-4 w-4" />
          New Session
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="px-2 pb-4">
          {loading ? (
            <div className="space-y-1.5 px-1 pt-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <p className="px-3 py-8 text-center text-xs text-muted-foreground">
              No sessions yet.
              <br />
              Start by entering a ticker below.
            </p>
          ) : (
            <div className="space-y-0.5 pt-1">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => onSelect(s.id)}
                  className={cn(
                    "group flex w-full items-start gap-2.5 rounded-md px-3 py-2.5 text-left transition-colors",
                    activeSessionId === s.id
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 opacity-60" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{s.title}</div>
                    <div className="mt-0.5 text-[11px] opacity-60">
                      {new Date(s.updated_at).toLocaleDateString()}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
