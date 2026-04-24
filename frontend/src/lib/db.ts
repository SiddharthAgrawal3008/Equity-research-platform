import { supabase } from "@/lib/supabase";

export interface Session {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
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

export async function createSession(userId: string, title: string): Promise<Session> {
  const { data, error } = await supabase
    .from("sessions")
    .insert({ user_id: userId, title })
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
