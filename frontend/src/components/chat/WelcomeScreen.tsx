"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import {
  WELCOME_MESSAGE,
  SUGGESTED_QUESTIONS,
  SUGGESTED_QUESTIONS_COUNT,
} from "@/lib/constants";

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void;
}

/** Fisher-Yates shuffle (non-mutating). */
function shuffle<T>(arr: readonly T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  // Pick random questions once on mount (client-only to avoid hydration mismatch)
  const [questions, setQuestions] = useState<string[]>([]);
  useEffect(() => {
    setQuestions(shuffle(SUGGESTED_QUESTIONS).slice(0, SUGGESTED_QUESTIONS_COUNT));
  }, []);

  return (
    <div className="flex flex-1 animate-[fade-in_0.3s_ease-out] flex-col items-center justify-center px-4 py-8">
      {/* Avatar */}
      <div className="mb-4 rounded-full ring-4 ring-emerald-200 shadow-lg">
        <Image
          src="/profgallade-avatar.jpg"
          alt="Prof. Gallade"
          width={96}
          height={96}
          className="rounded-full"
          priority
        />
      </div>

      {/* Title */}
      <h2 className="text-xl font-bold text-gray-800">Prof. Gallade</h2>
      <p className="mb-4 text-sm text-gray-500">Esperto Pokemon</p>

      {/* Welcome message */}
      <p className="mb-8 max-w-md text-center text-sm leading-relaxed text-gray-600">
        {WELCOME_MESSAGE}
      </p>

      {/* Suggested questions */}
      <div className="flex max-w-lg flex-wrap justify-center gap-2">
        {questions.map((q) => (
          <button
            key={q}
            onClick={() => onSuggestionClick(q)}
            className="rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm text-emerald-700 transition-colors hover:bg-emerald-100 hover:border-emerald-400 active:bg-emerald-200"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
