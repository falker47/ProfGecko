"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useChat } from "@/hooks/useChat";
import LoginPrompt from "../auth/LoginPrompt";
import CreditsExhausted from "../credits/CreditsExhausted";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

export default function ChatContainer() {
  const { user, token, credits } = useAuth();
  const {
    messages,
    isLoading,
    error,
    creditsExhausted,
    showLoginPrompt,
    sendMessage,
    clearChat,
    handleFeedback,
  } = useChat(token);

  // Show credits exhausted banner if:
  // - backend returned 402, OR
  // - user is logged in and credits are at 0
  const isOutOfCredits =
    creditsExhausted || (!!user && credits !== null && credits.total_available <= 0);

  return (
    <div className="flex h-full flex-col">
      <MessageList messages={messages} onFeedback={handleFeedback} />

      {isLoading && <TypingIndicator />}

      {error && (
        <div className="mx-4 mb-2 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
          {error}
        </div>
      )}

      {isOutOfCredits && <CreditsExhausted />}

      {showLoginPrompt && !user && <LoginPrompt />}

      <ChatInput
        onSend={sendMessage}
        disabled={isLoading || isOutOfCredits}
        placeholder={isOutOfCredits ? "Crediti esauriti..." : undefined}
      />
    </div>
  );
}
