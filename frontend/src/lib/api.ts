const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export interface PipelineRequest {
  ticker: string;
  session_id?: string;
  user_id?: string;
}

export async function runPipeline(req: PipelineRequest): Promise<any> {
  const res = await fetch(`${API_URL}/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Pipeline request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export interface ChatRequest {
  question: string;
  analysis_context: any;
}

export async function sendChat(req: ChatRequest): Promise<{ answer: string; model: string }> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
