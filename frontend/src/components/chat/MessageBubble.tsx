"use client";

import clsx from "clsx";
import Image from "next/image";
import Markdown from "react-markdown";
import type { Message } from "@/lib/types";
import { useLanguage } from "@/contexts/LanguageContext";

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (messageId: string, feedback: "V" | "F") => void;
}

export default function MessageBubble({ message, onFeedback }: MessageBubbleProps) {
  const { t } = useLanguage();
  const isUser = message.role === "user";

  // Hide empty assistant placeholder — the TypingIndicator handles this state
  if (!isUser && !message.content) return null;

  const showFeedback =
    !isUser && message.id !== "welcome" && message.entryId != null && message.content;

  return (
    <div className="animate-[slide-up_0.3s_ease-out]">
      <div
        className={clsx("flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}
      >
        {/* Avatar */}
        {isUser ? (
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-sm text-white">
            {t.you}
          </div>
        ) : (
          <Image
            src="/prof-gecko.webp"
            alt="Prof. Gecko"
            width={32}
            height={32}
            className="h-8 w-8 shrink-0 rounded-full"
          />
        )}

        {/* Bubble */}
        <div
          className={clsx(
            "max-w-[85%] rounded-2xl px-4 py-2 text-sm leading-relaxed sm:max-w-[80%]",
            isUser
              ? "bg-emerald-600 text-white"
              : "bg-white text-gray-800 shadow-sm ring-1 ring-gray-100 dark:bg-gray-800 dark:text-gray-200 dark:ring-gray-700",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none overflow-x-auto prose-p:my-1 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0 prose-headings:my-2 prose-table:my-2 prose-hr:my-2 prose-strong:font-semibold dark:prose-invert">
              <Markdown>{message.content || "..."}</Markdown>
            </div>
          )}
        </div>
      </div>

      {/* Feedback buttons */}
      {showFeedback && (
        <div className="ml-10 mt-1 flex gap-3">
          <button
            onClick={() => onFeedback?.(message.id, "V")}
            className={clsx(
              "flex items-center gap-1 text-xs transition-colors",
              message.feedback === "V"
                ? "text-emerald-600 font-medium"
                : "text-gray-400 hover:text-emerald-500 dark:text-gray-500",
            )}
          >
            <span className="text-sm">&#10003;</span> {t.feedbackCorrect}
          </button>
          <button
            onClick={() => onFeedback?.(message.id, "F")}
            className={clsx(
              "flex items-center gap-1 text-xs transition-colors",
              message.feedback === "F"
                ? "text-red-500 font-medium"
                : "text-gray-400 hover:text-red-400 dark:text-gray-500",
            )}
          >
            <span className="text-sm">&#10007;</span> {t.feedbackWrong}
          </button>
        </div>
      )}
    </div>
  );
}
