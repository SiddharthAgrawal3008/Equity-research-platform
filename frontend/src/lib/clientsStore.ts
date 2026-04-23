// Client workspace store — UI-only (localStorage). Backend wiring comes later.
import { useEffect, useState, useSyncExternalStore } from "react";

export type DocKind = "excel" | "pdf" | "word" | "powerpoint" | "transcript" | "other";
export type DocStatus = "uploading" | "parsing" | "ready" | "error";

export interface UploadedDoc {
  id: string;
  name: string;
  size: number;
  kind: DocKind;
  status: DocStatus;
  uploadedAt: number;
  pages?: number;
  summary?: string;
}

export interface ClientReport {
  id: string;
  ticker: string | null; // null for upload-only reports
  title: string;
  createdAt: number;
  rating: "BUY" | "HOLD" | "SELL";
  intrinsic?: number;
  upside?: number;
  sourceDocIds: string[];
}

export interface Client {
  id: string;
  name: string;
  organization?: string;
  notes?: string;
  createdAt: number;
  documents: UploadedDoc[];
  reports: ClientReport[];
}

const KEY = "equimind.clients.v1";

const seed = (): Client[] => [
  {
    id: "cl_acme",
    name: "Acme Capital Partners",
    organization: "$420M long/short fund",
    notes: "Focused on US large-cap tech and consumer.",
    createdAt: Date.now() - 1000 * 60 * 60 * 24 * 14,
    documents: [
      { id: "d1", name: "AAPL_FY24_10K.pdf", size: 4_182_000, kind: "pdf", status: "ready", uploadedAt: Date.now() - 86400000 * 10, pages: 142, summary: "FY24 annual report — Services 25% of revenue at 74% gross margin." },
      { id: "d2", name: "Internal_DCF_Model.xlsx", size: 387_400, kind: "excel", status: "ready", uploadedAt: Date.now() - 86400000 * 8, summary: "Three-statement model with sensitivity grid (sheet: DCF)." },
      { id: "d3", name: "Q4_Earnings_Transcript.pdf", size: 612_000, kind: "transcript", status: "ready", uploadedAt: Date.now() - 86400000 * 5, pages: 28, summary: "Earnings call transcript — management tone +4.2pts YoY." },
    ],
    reports: [
      { id: "r1", ticker: "AAPL", title: "AAPL — Verified with internal model", createdAt: Date.now() - 86400000 * 4, rating: "BUY", intrinsic: 198.4, upside: 12.2, sourceDocIds: ["d1", "d2", "d3"] },
    ],
  },
  {
    id: "cl_oakwood",
    name: "Oakwood Family Office",
    organization: "Single-family office",
    notes: "Long-only, dividend-focused mandate.",
    createdAt: Date.now() - 1000 * 60 * 60 * 24 * 6,
    documents: [],
    reports: [],
  },
];

const load = (): Client[] => {
  if (typeof window === "undefined") return seed();
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) {
      const s = seed();
      localStorage.setItem(KEY, JSON.stringify(s));
      return s;
    }
    return JSON.parse(raw) as Client[];
  } catch {
    return seed();
  }
};

let state: Client[] = load();
const listeners = new Set<() => void>();

const persist = () => {
  localStorage.setItem(KEY, JSON.stringify(state));
  listeners.forEach((l) => l());
};

const subscribe = (l: () => void) => {
  listeners.add(l);
  return () => listeners.delete(l);
};

const getSnapshot = () => state;

export const useClients = () => useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

export const useClient = (id: string) => {
  const all = useClients();
  return all.find((c) => c.id === id);
};

const uid = (p: string) => `${p}_${Math.random().toString(36).slice(2, 9)}`;

export const createClient = (input: { name: string; organization?: string; notes?: string }) => {
  const c: Client = {
    id: uid("cl"),
    name: input.name,
    organization: input.organization,
    notes: input.notes,
    createdAt: Date.now(),
    documents: [],
    reports: [],
  };
  state = [c, ...state];
  persist();
  return c;
};

export const deleteClient = (id: string) => {
  state = state.filter((c) => c.id !== id);
  persist();
};

export const kindFromName = (name: string): DocKind => {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["xlsx", "xls", "csv"].includes(ext)) return "excel";
  if (["pdf"].includes(ext)) return "pdf";
  if (["doc", "docx"].includes(ext)) return "word";
  if (["ppt", "pptx", "key"].includes(ext)) return "powerpoint";
  if (["txt", "md", "vtt", "srt"].includes(ext)) return "transcript";
  return "other";
};

export const addDocuments = (clientId: string, files: File[]) => {
  const newDocs: UploadedDoc[] = files.map((f) => ({
    id: uid("d"),
    name: f.name,
    size: f.size,
    kind: kindFromName(f.name),
    status: "uploading",
    uploadedAt: Date.now(),
  }));

  state = state.map((c) =>
    c.id === clientId ? { ...c, documents: [...newDocs, ...c.documents] } : c,
  );
  persist();

  // Mock async parse pipeline
  newDocs.forEach((d, i) => {
    setTimeout(() => updateDoc(clientId, d.id, { status: "parsing" }), 400 + i * 150);
    setTimeout(
      () =>
        updateDoc(clientId, d.id, {
          status: "ready",
          pages: d.kind === "pdf" || d.kind === "word" ? 12 + Math.floor(Math.random() * 80) : undefined,
          summary: mockSummary(d.kind, d.name),
        }),
      1600 + i * 250,
    );
  });

  return newDocs;
};

export const updateDoc = (clientId: string, docId: string, patch: Partial<UploadedDoc>) => {
  state = state.map((c) =>
    c.id === clientId
      ? { ...c, documents: c.documents.map((d) => (d.id === docId ? { ...d, ...patch } : d)) }
      : c,
  );
  persist();
};

export const removeDoc = (clientId: string, docId: string) => {
  state = state.map((c) =>
    c.id === clientId ? { ...c, documents: c.documents.filter((d) => d.id !== docId) } : c,
  );
  persist();
};

export const addReport = (clientId: string, r: Omit<ClientReport, "id" | "createdAt">) => {
  const report: ClientReport = { ...r, id: uid("r"), createdAt: Date.now() };
  state = state.map((c) =>
    c.id === clientId ? { ...c, reports: [report, ...c.reports] } : c,
  );
  persist();
  return report;
};

const mockSummary = (kind: DocKind, name: string) => {
  switch (kind) {
    case "excel":
      return `Parsed ${1 + Math.floor(Math.random() * 6)} sheets · detected DCF inputs and sensitivity grid.`;
    case "pdf":
      return `OCR complete · extracted financial tables and management commentary.`;
    case "word":
      return `Document parsed · ready to feed into memo and risk engines.`;
    case "powerpoint":
      return `Slide deck parsed · charts and bullet points indexed.`;
    case "transcript":
      return `Speaker-labeled transcript ready for sentiment scoring.`;
    default:
      return `File "${name}" indexed for retrieval.`;
  }
};

// Convenience hook: format file size
export const useFormatBytes = () => (b: number) => {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
};

// Re-export for components that just need the formatter without the hook wrapper
export const formatBytes = (b: number) => {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(1)} MB`;
};

// Stub to keep React happy if unused elsewhere
export const _ = { useEffect, useState };
