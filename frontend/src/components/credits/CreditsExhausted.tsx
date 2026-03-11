"use client";

import { useLanguage } from "@/contexts/LanguageContext";

export default function CreditsExhausted() {
  const { t } = useLanguage();

  return (
    <div className="mx-4 mb-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-center dark:border-red-800 dark:bg-red-950">
      <p className="text-sm font-medium text-red-700 dark:text-red-400">
        {t.creditsExhaustedTitle}
      </p>
      <p className="mt-1 text-xs text-red-600 dark:text-red-400">
        {t.creditsExhaustedMessage}
      </p>
    </div>
  );
}
