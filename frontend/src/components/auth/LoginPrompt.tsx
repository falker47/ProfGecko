"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

export default function LoginPrompt() {
  const { renderGoogleButton } = useAuth();
  const { t } = useLanguage();
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (btnRef.current) {
      renderGoogleButton(btnRef.current);
    }
  }, [renderGoogleButton]);

  // Split the translated message around the bold part to insert <strong>
  const fullText = t.loginPromptText(t.loginPromptBold);
  const parts = fullText.split(t.loginPromptBold);

  return (
    <div className="mx-4 mb-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-center dark:border-emerald-800 dark:bg-emerald-950">
      <p className="mb-2 text-sm text-emerald-800 dark:text-emerald-200">
        {parts[0]}
        <strong>{t.loginPromptBold}</strong>
        {parts[1]}
      </p>
      <div className="flex justify-center">
        <div ref={btnRef} />
      </div>
    </div>
  );
}
