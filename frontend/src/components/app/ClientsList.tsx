import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Search, Users, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useClients, createClient } from "@/lib/clientsStore";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export const ClientsList = () => {
  const { user } = useAuth();
  const { clients, loading } = useClients();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const filtered = clients.filter((c) =>
    (c.name + " " + (c.organization ?? "")).toLowerCase().includes(q.toLowerCase()),
  );

  if (loading) {
    return (
      <div className="container flex items-center justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container py-8 lg:py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Workspace</div>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">Private Clients</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Each client has their own document vault and research history.
          </p>
        </div>
        <NewClientButton open={open} setOpen={setOpen} userId={user?.id ?? ""} />
      </div>

      <div className="mt-6 flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search clients..."
            className="pl-9"
          />
        </div>
        <span className="text-xs text-muted-foreground">
          {filtered.length} {filtered.length === 1 ? "client" : "clients"}
        </span>
      </div>

      {filtered.length === 0 ? (
        <Card className="mt-8 flex flex-col items-center gap-3 border-dashed border-border bg-surface p-12 text-center">
          <Users className="h-8 w-8 text-muted-foreground" />
          <div className="font-semibold">No clients yet</div>
          <p className="max-w-sm text-sm text-muted-foreground">
            Create a client to start uploading their documents and generating private research.
          </p>
          <NewClientButton open={open} setOpen={setOpen} userId={user?.id ?? ""} />
        </Card>
      ) : (
        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <Link key={c.id} to={`/app/clients/${c.id}`}>
              <Card className="group h-full border-border bg-card p-6 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-elevated">
                <div className="flex items-start justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-navy font-display text-base font-semibold text-primary-foreground">
                    {c.name.charAt(0)}
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-accent" />
                </div>
                <h3 className="mt-4 font-semibold leading-tight">{c.name}</h3>
                {c.organization && (
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">{c.organization}</p>
                )}
                <div className="mt-5 border-t border-border pt-4 text-xs text-muted-foreground">
                  {new Date(c.created_at).toLocaleDateString()}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

const NewClientButton = ({
  open,
  setOpen,
  userId,
}: {
  open: boolean;
  setOpen: (v: boolean) => void;
  userId: string;
}) => {
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !userId) return;
    setSaving(true);
    try {
      await createClient(userId, {
        name: name.trim(),
        organization: org.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      toast.success(`Client "${name}" created`);
      setName("");
      setOrg("");
      setNotes("");
      setOpen(false);
    } catch {
      toast.error("Failed to create client");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="hero">
          <Plus className="h-4 w-4" /> New client
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={submit}>
          <DialogHeader>
            <DialogTitle>Create a private client</DialogTitle>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cname">Client name</Label>
              <Input id="cname" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Acme Capital Partners" required autoFocus />
            </div>
            <div className="space-y-2">
              <Label htmlFor="corg">Organization (optional)</Label>
              <Input id="corg" value={org} onChange={(e) => setOrg(e.target.value)} placeholder="e.g. $200M long/short fund" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cnotes">Internal notes (optional)</Label>
              <Textarea id="cnotes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="Mandate, focus area..." />
            </div>
          </div>
          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="hero" disabled={saving}>
              {saving ? "Creating…" : "Create client"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
