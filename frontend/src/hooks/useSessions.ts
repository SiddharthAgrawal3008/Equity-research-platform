import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { createSession as dbCreateSession, getSessions, type Session } from "@/lib/db";
import { supabase } from "@/lib/supabase";

export function useSessions() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    getSessions(user.id)
      .then(setSessions)
      .finally(() => setLoading(false));

    const channel = supabase
      .channel("sessions-changes")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "sessions",
          filter: `user_id=eq.${user.id}`,
        },
        () => getSessions(user.id).then(setSessions),
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [user]);

  const createSession = useCallback(
    async (title: string) => {
      if (!user) throw new Error("Not authenticated");
      const session = await dbCreateSession(user.id, title);
      setSessions((prev) =>
        prev.some((s) => s.id === session.id) ? prev : [session, ...prev],
      );
      return session;
    },
    [user],
  );

  return { sessions, loading, createSession };
}
