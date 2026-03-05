"use client";

import { useChat } from "@/hooks/useChat";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

export default function ChatContainer() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} />

      {isLoading && <TypingIndicator />}

      {error && (
        <div className="mx-4 mb-2 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      )}

      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
