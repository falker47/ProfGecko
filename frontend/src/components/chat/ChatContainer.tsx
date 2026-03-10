"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useChat } from "@/hooks/useChat";
import LoginPrompt from "../auth/LoginPrompt";
import CreditsExhausted from "../credits/CreditsExhausted";
import ChatInput from "./ChatInput";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";
import WelcomeScreen from "./WelcomeScreen";

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

  const showWelcome = messages.length === 1 && messages[0].id === "welcome";

  return (
    <div className="flex h-full flex-col">
      {showWelcome ? (
        <WelcomeScreen onSuggestionClick={sendMessage} />
      ) : (
        <>
          {/* New chat bar */}
          <div className="flex justify-center border-b border-gray-100 py-1.5">
            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-3.5 w-3.5"
              >
                <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
              </svg>
              Nuova chat
            </button>
          </div>

          <MessageList messages={messages} onFeedback={handleFeedback} />

          {isLoading && <TypingIndicator />}

          {error && (
            <div className="mx-4 mb-2 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">
              {error}
            </div>
          )}

          {isOutOfCredits && <CreditsExhausted />}

          {showLoginPrompt && !user && <LoginPrompt />}
        </>
      )}

      <ChatInput
        onSend={sendMessage}
        disabled={isLoading || isOutOfCredits}
        placeholder={isOutOfCredits ? "Crediti esauriti..." : undefined}
      />
    </div>
  );
}
