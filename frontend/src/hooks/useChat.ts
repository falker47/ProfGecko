"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { streamChat, submitFeedback as apiFeedback } from "@/lib/api";
import { ANONYMOUS_LIMIT } from "@/lib/constants";
import type { Message } from "@/lib/types";
import { useLanguage } from "@/contexts/LanguageContext";

const ANON_COUNT_KEY = "profgallade_anon_count";

function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}

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
  const { locale, t } = useLanguage();

  // Welcome message reactive to language
  const welcomeMsg = useMemo<Message>(
    () => ({
      id: "welcome",
      role: "assistant",
      content: t.welcomeMessage,
      timestamp: new Date(),
    }),
    [t.welcomeMessage],
  );

  const [messages, setMessages] = useState<Message[]>([welcomeMsg]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creditsExhausted, setCreditsExhausted] = useState(false);
  const [showLoginPrompt, setShowLoginPrompt] = useState(false);
  const abortRef = useRef(false);

  // When locale changes and we're still on the welcome screen, update the message
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === "welcome") {
        return [welcomeMsg];
      }
      return prev;
    });
  }, [locale, welcomeMsg]);

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
        translations: t,
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
        onDone: (_gen?: number, entryId?: number) => {
          if (entryId) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, entryId } : m,
              ),
            );
          }
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
    [isLoading, messages, authToken, t],
  );

  const clearChat = useCallback(() => {
    setMessages([welcomeMsg]);
    setError(null);
    setCreditsExhausted(false);
    setShowLoginPrompt(false);
  }, [welcomeMsg]);

  const dismissLoginPrompt = useCallback(() => {
    setShowLoginPrompt(false);
  }, []);

  const handleFeedback = useCallback(
    async (messageId: string, feedback: "V" | "F") => {
      const msg = messages.find((m) => m.id === messageId);
      if (!msg?.entryId) return;

      // Toggle: clicking same feedback removes it
      const newFeedback = msg.feedback === feedback ? null : feedback;

      // Optimistic UI update
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, feedback: newFeedback } : m,
        ),
      );

      // Only call API when setting (not unsetting)
      if (newFeedback) {
        try {
          await apiFeedback(msg.entryId, newFeedback);
        } catch {
          // Revert on error
          setMessages((prev) =>
            prev.map((m) =>
              m.id === messageId ? { ...m, feedback: msg.feedback } : m,
            ),
          );
        }
      }
    },
    [messages],
  );

  return {
    messages,
    isLoading,
    error,
    creditsExhausted,
    showLoginPrompt,
    sendMessage,
    clearChat,
    dismissLoginPrompt,
    handleFeedback,
  };
}
