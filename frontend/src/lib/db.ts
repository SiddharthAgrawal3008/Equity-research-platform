import { supabase } from "@/lib/supabase";

export interface Session {
  id: string;
  user_id: string;
  title: string;
  client_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Client {
  id: string;
  user_id: string;
  name: string;
  organization: string | null;
  notes: string | null;
  created_at: string;
}

export interface ClientDocument {
  id: string;
  client_id: string;
  user_id: string;
  name: string;
  size: number;
  kind: string;
  status: string;
  storage_path: string | null;
  parsed_data: Record<string, unknown> | null;
  uploaded_at: string;
}

export interface ClientSessionEntry {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  ticker: string | null;
}

export interface Message {
  id: string;
  session_id: string;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "research" | "error";
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export async function createSession(userId: string, title: string, clientId?: string): Promise<Session> {
  const { data, error } = await supabase
    .from("sessions")
    .insert({ user_id: userId, title, ...(clientId ? { client_id: clientId } : {}) })
    .select()
    .single();
  if (error) throw error;
  return data as Session;
}

export async function getSessions(userId: string): Promise<Session[]> {
  const { data, error } = await supabase
    .from("sessions")
    .select("*")
    .eq("user_id", userId)
    .order("updated_at", { ascending: false });
  if (error) throw error;
  return (data ?? []) as Session[];
}

export async function addMessage(
  sessionId: string,
  userId: string,
  role: "user" | "assistant",
  content: string,
  type: "text" | "research" | "error",
  metadata?: Record<string, unknown>,
): Promise<Message> {
  const { data, error } = await supabase
    .from("messages")
    .insert({ session_id: sessionId, user_id: userId, role, content, type, metadata: metadata ?? null })
    .select()
    .single();
  if (error) throw error;
  return data as Message;
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  const { data, error } = await supabase
    .from("messages")
    .select("*")
    .eq("session_id", sessionId)
    .order("created_at", { ascending: true });
  if (error) throw error;
  return (data ?? []) as Message[];
}

export async function saveResearchResult(
  sessionId: string,
  userId: string,
  ticker: string,
  data: unknown,
): Promise<void> {
  const { error } = await supabase
    .from("research_results")
    .insert({ session_id: sessionId, user_id: userId, ticker, data });
  if (error) throw error;
}

// ── Client CRUD ──────────────────────────────────────────────────────────────

export async function createClient(
  userId: string,
  input: { name: string; organization?: string; notes?: string },
): Promise<Client> {
  const { data, error } = await supabase
    .from("clients")
    .insert({ user_id: userId, name: input.name, organization: input.organization ?? null, notes: input.notes ?? null })
    .select()
    .single();
  if (error) throw error;
  return data as Client;
}

export async function getClients(userId: string): Promise<Client[]> {
  const { data, error } = await supabase
    .from("clients")
    .select("*")
    .eq("user_id", userId)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data ?? []) as Client[];
}

export async function getClient(
  clientId: string,
): Promise<(Client & { documents: ClientDocument[] }) | null> {
  const [clientRes, docsRes] = await Promise.all([
    supabase.from("clients").select("*").eq("id", clientId).single(),
    supabase.from("client_documents").select("*").eq("client_id", clientId).order("uploaded_at", { ascending: false }),
  ]);
  if (clientRes.error) return null;
  return {
    ...(clientRes.data as Client),
    documents: (docsRes.data ?? []) as ClientDocument[],
  };
}

export async function deleteClient(clientId: string): Promise<void> {
  const { error } = await supabase.from("clients").delete().eq("id", clientId);
  if (error) throw error;
}

// ── Document CRUD ─────────────────────────────────────────────────────────────

export async function addDocument(
  clientId: string,
  userId: string,
  file: File,
  kind: string,
  parsedData?: Record<string, unknown>,
): Promise<ClientDocument> {
  const docId = crypto.randomUUID();
  const ext = file.name.split(".").pop() ?? "bin";
  const storagePath = `${userId}/${clientId}/${docId}.${ext}`;

  const { error: storageError } = await supabase.storage
    .from("client-documents")
    .upload(storagePath, file);
  if (storageError) throw storageError;

  const { data, error } = await supabase
    .from("client_documents")
    .insert({
      id: docId,
      client_id: clientId,
      user_id: userId,
      name: file.name,
      size: file.size,
      kind,
      status: "ready",
      storage_path: storagePath,
      parsed_data: parsedData ?? null,
    })
    .select()
    .single();
  if (error) throw error;
  return data as ClientDocument;
}

export async function removeDocument(docId: string, storagePath?: string | null): Promise<void> {
  if (storagePath) {
    await supabase.storage.from("client-documents").remove([storagePath]);
  }
  const { error } = await supabase.from("client_documents").delete().eq("id", docId);
  if (error) throw error;
}

// ── Client sessions (research history) ───────────────────────────────────────

export async function getClientSessions(clientId: string): Promise<ClientSessionEntry[]> {
  const { data, error } = await supabase
    .from("sessions")
    .select("id, title, created_at, updated_at, research_results(ticker)")
    .eq("client_id", clientId)
    .order("updated_at", { ascending: false });
  if (error) throw error;
  return ((data ?? []) as Array<{
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    research_results: Array<{ ticker: string }>;
  }>).map((s) => ({
    id: s.id,
    title: s.title,
    created_at: s.created_at,
    updated_at: s.updated_at,
    ticker: s.research_results?.[0]?.ticker ?? null,
  }));
}
