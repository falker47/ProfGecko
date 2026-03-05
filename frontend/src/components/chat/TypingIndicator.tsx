export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-2 text-xs text-gray-400">
      <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
      <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
      <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
      <span className="ml-1">Prof. Gallade sta pensando</span>
    </div>
  );
}
