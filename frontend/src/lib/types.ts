export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  entryId?: number;
  feedback?: "V" | "F" | null;
}

export interface ChatRequest {
  message: string;
  chat_history: { role: string; content: string }[];
}

export interface ChatResponse {
  answer: string;
  generation_used: number;
}

// --- Auth & Credits ---

export interface User {
  id: string;
  name: string;
  email: string;
  picture_url: string;
}

export interface CreditBalance {
  daily_free_remaining: number;
  daily_free_total: number;
  paid_credits: number;
  total_available: number;
}

export interface AuthResponse {
  access_token: string;
  user: User;
  credits: CreditBalance;
}
