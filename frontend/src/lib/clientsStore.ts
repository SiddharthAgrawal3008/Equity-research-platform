import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabase";
import {
  createClient as dbCreateClient,
  deleteClient as dbDeleteClient,
  getClients,
  getClient,
  addDocument as dbAddDocument,
  removeDocument as dbRemoveDocument,
  getClientSessions,
  type Client,
  type ClientDocument,
  type ClientSessionEntry,
} from "@/lib/db";

export type DocKind = "excel" | "pdf" | "word" | "powerpoint" | "transcript" | "other";
export type DocStatus = "uploading" | "parsing" | "ready" | "error";

export type UploadedDoc = ClientDocument;
export type { Client, ClientDocument, ClientSessionEntry };

export const kindFromName = (name: string): DocKind => {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["xlsx", "xls", "csv"].includes(ext)) return "excel";
  if (ext === "pdf") return "pdf";
  if (["doc", "docx"].includes(ext)) return "word";
  if (["ppt", "pptx", "key"].includes(ext)) return "powerpoint";
  if (["txt", "md", "vtt", "srt"].includes(ext)) return "transcript";
  return "other";
};

export const formatBytes = (b: number) => {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
};

export const useFormatBytes = () => formatBytes;

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useClients() {
  const { user } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { setLoading(false); return; }

    getClients(user.id)
      .then(setClients)
      .finally(() => setLoading(false));

    const channel = supabase
      .channel("clients-changes")
      .on("postgres_changes", {
        event: "*", schema: "public", table: "clients",
        filter: `user_id=eq.${user.id}`,
      }, () => getClients(user.id).then(setClients))
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [user]);

  return { clients, loading };
}

export function useClient(clientId: string) {
  const [data, setData] = useState<(Client & { documents: ClientDocument[] }) | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = () => {
    if (!clientId) return;
    getClient(clientId)
      .then(setData)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();

    const channel = supabase
      .channel(`client-docs-${clientId}`)
      .on("postgres_changes", {
        event: "*", schema: "public", table: "client_documents",
        filter: `client_id=eq.${clientId}`,
      }, reload)
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [clientId]);

  return { client: data, loading, reload };
}

export function useClientSessions(clientId: string) {
  const [sessions, setSessions] = useState<ClientSessionEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!clientId) { setLoading(false); return; }

    getClientSessions(clientId)
      .then(setSessions)
      .finally(() => setLoading(false));

    const channel = supabase
      .channel(`client-sessions-${clientId}`)
      .on("postgres_changes", {
        event: "*", schema: "public", table: "sessions",
        filter: `client_id=eq.${clientId}`,
      }, () => getClientSessions(clientId).then(setSessions))
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [clientId]);

  return { sessions, loading };
}

// ── Actions ───────────────────────────────────────────────────────────────────

export async function createClient(
  userId: string,
  input: { name: string; organization?: string; notes?: string },
) {
  return dbCreateClient(userId, input);
}

export async function deleteClient(clientId: string) {
  return dbDeleteClient(clientId);
}

export async function addDocuments(clientId: string, userId: string, files: File[]) {
  const results: ClientDocument[] = [];
  for (const file of files) {
    const doc = await dbAddDocument(clientId, userId, file, kindFromName(file.name));
    results.push(doc);
  }
  return results;
}

export async function removeDoc(docId: string, storagePath?: string | null) {
  return dbRemoveDocument(docId, storagePath);
}
