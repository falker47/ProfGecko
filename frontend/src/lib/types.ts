export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  chat_history: { role: string; content: string }[];
}

export interface ChatResponse {
  answer: string;
  generation_used: number;
}
