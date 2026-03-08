"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api";
import { ANONYMOUS_LIMIT, WELCOME_MESSAGE } from "@/lib/constants";
import type { Message } from "@/lib/types";

const ANON_COUNT_KEY = "profgallade_anon_count";

function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}

const welcomeMessage: Message = {
  id: "welcome",
  role: "assistant",
  content: WELCOME_MESSAGE,
  timestamp: new Date(),
};

function getAnonCount(): number {
  try {
    return parseInt(sessionStorage.getItem(ANON_COUNT_KEY) || "0", 10);
  } catch {
    return 0;
  }
}

function incrementAnonCount(): number {
  const next = getAnonCount() + 1;
  try {
    sessionStorage.setItem(ANON_COUNT_KEY, String(next));
  } catch {
    // sessionStorage unavailable
  }
  return next;
}

export function useChat(authToken?: string | null) {
  const [messages, setMessages] = useState<Message[]>([welcomeMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creditsExhausted, setCreditsExhausted] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const abortRef = useRef(false);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || isLoading) return;

      // Anonymous soft limit: after ANONYMOUS_LIMIT messages, show login prompt
      if (!authToken) {
        const count = incrementAnonCount();
        if (count > ANONYMOUS_LIMIT) {
          setShowLoginPrompt(true);
          // Still allow sending — it's a soft limit
        }
      }

      setError(null);
      setCreditsExhausted(false);
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

      await streamChat({
        message: text.trim(),
        history,
        authToken,
        // onToken
        onToken: (token) => {
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
        onDone: () => {
          setIsLoading(false);
        },
        // onError
        onError: (errMsg) => {
          setError(errMsg);
          setIsLoading(false);
          // Remove the empty assistant message on error
          setMessages((prev) => prev.filter((m) => m.id !== assistantId));
        },
        // onCreditsExhausted
        onCreditsExhausted: () => {
          setCreditsExhausted(true);
        },
      });
    },
    [isLoading, messages, authToken],
  );

  const clearChat = useCallback(() => {
    setMessages([welcomeMessage]);
    setError(null);
    setCreditsExhausted(false);
    setShowLoginPrompt(false);
  }, []);

  const dismissLoginPrompt = useCallback(() => {
    setShowLoginPrompt(false);
  }, []);

  return {
    messages,
    isLoading,
    error,
    creditsExhausted,
    showLoginPrompt,
    sendMessage,
    clearChat,
    dismissLoginPrompt,
  };
}
