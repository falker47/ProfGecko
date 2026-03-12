import Image from "next/image";

export default function TypingIndicator() {
  return (
    <div className="flex animate-[fade-in_0.3s_ease-out] items-start gap-2 px-4 py-2">
      <Image
        src="/prof-gecko.webp"
        alt="Prof. Gecko"
        width={32}
        height={32}
        className="h-8 w-8 shrink-0 rounded-full"
      />
      <div className="flex items-center gap-1.5 rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-gray-100 dark:bg-gray-800 dark:ring-gray-700">
        <span
          className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-[dot-pulse_1.4s_ease-in-out_infinite]"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-[dot-pulse_1.4s_ease-in-out_infinite]"
          style={{ animationDelay: "200ms" }}
        />
        <span
          className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-[dot-pulse_1.4s_ease-in-out_infinite]"
          style={{ animationDelay: "400ms" }}
        />
      </div>
    </div>
  );
}
