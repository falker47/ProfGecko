import clsx from "clsx";
import Markdown from "react-markdown";
import type { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={clsx("flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div
        className={clsx(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm",
          isUser ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-700",
        )}
      >
        {isUser ? "Tu" : "PG"}
      </div>

      {/* Bubble */}
      <div
        className={clsx(
          "max-w-[80%] rounded-2xl px-4 py-2 text-sm leading-relaxed",
          isUser
            ? "bg-emerald-600 text-white"
            : "bg-white text-gray-800 shadow-sm ring-1 ring-gray-100",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
            <Markdown>{message.content || "..."}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}
