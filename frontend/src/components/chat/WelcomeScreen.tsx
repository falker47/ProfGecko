"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { SUGGESTED_QUESTIONS_COUNT } from "@/lib/constants";
import { useLanguage } from "@/contexts/LanguageContext";

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
  const { locale, t } = useLanguage();

  // Pick random questions on mount and re-shuffle when language changes
  const [questions, setQuestions] = useState<string[]>([]);
  useEffect(() => {
    setQuestions(shuffle(t.suggestedQuestions).slice(0, SUGGESTED_QUESTIONS_COUNT));
  }, [locale, t.suggestedQuestions]);

  return (
    <div className="flex flex-1 animate-[fade-in_0.3s_ease-out] flex-col items-center justify-center px-4 py-8">
      {/* Avatar */}
      <div className="mb-5 rounded-full shadow-xl ring-4 ring-emerald-200/70 dark:ring-emerald-700/70">
        <Image
          src="/profgallade-avatar.jpg"
          alt="Prof. Gallade"
          width={128}
          height={128}
          className="rounded-full"
          priority
        />
      </div>

      {/* Title */}
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">{t.siteTitle}</h2>

      {/* Subtitle badge */}
      <span className="mb-4 mt-1.5 inline-block rounded-full bg-emerald-100 px-3 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
        {t.siteSubtitle}
      </span>

      {/* Welcome message */}
      <p className="mb-8 max-w-lg text-center text-base leading-relaxed text-gray-600 dark:text-gray-400">
        {t.welcomeMessage}
      </p>

      {/* Suggested questions */}
      <div className="grid w-full max-w-lg gap-2 sm:grid-cols-2">
        {questions.map((q) => (
          <button
            key={q}
            onClick={() => onSuggestionClick(q)}
            className="group flex items-start gap-2 rounded-lg border border-gray-200 bg-white px-3.5 py-2.5 text-left text-sm text-gray-700 shadow-sm transition-all hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md active:translate-y-0 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-emerald-600"
          >
            <span className="mt-0.5 shrink-0 text-emerald-500 transition-colors group-hover:text-emerald-600 dark:text-emerald-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path fillRule="evenodd" d="M2 10a.75.75 0 0 1 .75-.75h12.59l-2.1-1.95a.75.75 0 1 1 1.02-1.1l3.5 3.25a.75.75 0 0 1 0 1.1l-3.5 3.25a.75.75 0 1 1-1.02-1.1l2.1-1.95H2.75A.75.75 0 0 1 2 10Z" clipRule="evenodd" />
              </svg>
            </span>
            <span>{q}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
