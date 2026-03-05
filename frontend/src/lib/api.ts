import { API_BASE_URL, MAX_HISTORY_MESSAGES } from "./constants";
import type { Message } from "./types";

export async function streamChat(
  message: string,
  history: Message[],
  onToken: (token: string) => void,
  onDone: (generationUsed?: number) => void,
  onError: (error: string) => void,
): Promise<void> {
  const chatHistory = history.slice(-MAX_HISTORY_MESSAGES).map((m) => ({
    role: m.role,
    content: m.content,
  }));

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, chat_history: chatHistory }),
    });
  } catch {
    onError("Impossibile connettersi al server. Verifica che il backend sia avviato.");
    return;
  }

  if (!response.ok) {
    onError(`Errore dal server: ${response.status}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("Streaming non supportato dal browser.");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          const event = line.slice(7).trim();

          // The next data: line contains the payload
          // We'll handle it in the data processing below
          if (event === "done") {
            // Will be processed when we see the data line
          }
        } else if (line.startsWith("data: ")) {
          const dataStr = line.slice(6).trim();
          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            if ("token" in data) {
              onToken(data.token);
            } else if ("generation_used" in data) {
              onDone(data.generation_used);
              return;
            }
          } catch {
            // Ignore malformed JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  onDone();
}
