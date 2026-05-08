export type MessageRole = "user" | "system" | "assistant";

export type CardType =
  | "company-header"
  | "valuation"
  | "risk"
  | "nlp"
  | "report"
  | "pipeline-status";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content?: string;
  card?: {
    type: CardType;
    data: any;
    engineStatus?: "running" | "success" | "failed";
  };
  timestamp: Date;
}

export function createId(): string {
  return Math.random().toString(36).slice(2, 10);
}
