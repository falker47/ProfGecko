"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import { WELCOME_MESSAGE } from "@/lib/constants";
import type { Message } from "@/lib/types";

function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}

const welcomeMessage: Message = {
  id: "welcome",
  role: "assistant",
  content: WELCOME_MESSAGE,
  timestamp: new Date(),
};

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([welcomeMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      setError(null);
      abortRef.current = false;

      // Add user message
      const userMsg: Message = {
        id: generateId(),
        role: "user",
        content: text.trim(),
        timestamp: new Date(),
      };

      const assistantId = generateId();

      setMessages((prev) => [
        ...prev,
        userMsg,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          timestamp: new Date(),
        },
      ]);

      setIsLoading(true);

      // Get current history (excluding the empty assistant message)
      const history = [...messages, userMsg].filter(
        (m) => m.id !== "welcome",
      );

      await streamChat(
        text.trim(),
        history,
        // onToken
        (token) => {
          if (abortRef.current) return;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m,
            ),
          );
        },
        // onDone
        () => {
          setIsLoading(false);
        },
        // onError
        (errMsg) => {
          setError(errMsg);
          setIsLoading(false);
          // Remove the empty assistant message on error
          setMessages((prev) => prev.filter((m) => m.id !== assistantId));
        },
      );
    },
    [isLoading, messages],
  );

  const clearChat = useCallback(() => {
    setMessages([welcomeMessage]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearChat };
}
