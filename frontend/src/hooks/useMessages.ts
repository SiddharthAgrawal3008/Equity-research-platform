import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { addMessage as dbAddMessage, getMessages, type Message } from "@/lib/db";
import { supabase } from "@/lib/supabase";

export function useMessages(sessionId: string | null) {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    setLoading(true);
    getMessages(sessionId)
      .then(setMessages)
      .finally(() => setLoading(false));

    const channel = supabase
      .channel(`messages-${sessionId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `session_id=eq.${sessionId}`,
        },
        (payload) =>
          setMessages((prev) => {
            const msg = payload.new as Message;
            return prev.some((m) => m.id === msg.id) ? prev : [...prev, msg];
          }),
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [sessionId]);

  const addMessage = useCallback(
    async (
      role: "user" | "assistant",
      content: string,
      type: "text" | "research" | "error",
      metadata?: Record<string, unknown>,
    ) => {
      if (!sessionId || !user) throw new Error("No active session");
      return dbAddMessage(sessionId, user.id, role, content, type, metadata);
    },
    [sessionId, user],
  );

  return { messages, loading, addMessage };
}
