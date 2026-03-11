"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { useTheme } from "@/contexts/ThemeContext";
import UserMenu from "./UserMenu";

export default function Header() {
  const { user, isLoading, renderGoogleButton } = useAuth();
  const { locale, t, setLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user && !isLoading && btnRef.current) {
      renderGoogleButton(btnRef.current);
    }
  }, [user, isLoading, renderGoogleButton]);

  return (
    <header className="bg-emerald-700 text-white shadow-md dark:bg-emerald-900">
      <div className="mx-auto flex max-w-3xl items-center gap-2 px-4 py-3 sm:gap-3">
        <Image
          src="/profgallade-avatar.jpg"
          alt="Prof. Gallade"
          width={40}
          height={40}
          className="h-8 w-8 rounded-full ring-1 ring-emerald-400 sm:h-10 sm:w-10 sm:ring-2"
        />
        <h1 className="flex-1 truncate text-lg font-bold leading-tight">{t.siteTitle}</h1>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-full p-1.5 text-emerald-200 transition-colors hover:bg-emerald-600 hover:text-white dark:hover:bg-emerald-800"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path fillRule="evenodd" d="M7.455 2.004a.75.75 0 0 1 .26.77 7 7 0 0 0 9.958 7.967.75.75 0 0 1 1.067.853A8.5 8.5 0 1 1 6.647 1.921a.75.75 0 0 1 .808.083Z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
              <path d="M10 2a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 2ZM10 15a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 10 15ZM10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM15.657 5.404a.75.75 0 1 0-1.06-1.06l-1.061 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM6.464 14.596a.75.75 0 1 0-1.06-1.06l-1.06 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06ZM18 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 18 10ZM5 10a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 5 10ZM14.596 15.657a.75.75 0 0 0 1.06-1.06l-1.06-1.061a.75.75 0 1 0-1.06 1.06l1.06 1.06ZM5.404 6.464a.75.75 0 0 0 1.06-1.06l-1.06-1.06a.75.75 0 1 0-1.06 1.06l1.06 1.06Z" />
            </svg>
          )}
        </button>

        {/* Language toggle */}
        <div className="flex items-center rounded-full bg-emerald-800/60 p-0.5 text-xs font-medium">
          <button
            onClick={() => setLanguage("it")}
            className={`rounded-full px-2 py-1 transition-colors ${
              locale === "it"
                ? "bg-emerald-500 text-white shadow-sm"
                : "text-emerald-300 hover:text-white"
            }`}
            aria-label="Italiano"
            aria-pressed={locale === "it"}
          >
            IT
          </button>
          <button
            onClick={() => setLanguage("en")}
            className={`rounded-full px-2 py-1 transition-colors ${
              locale === "en"
                ? "bg-emerald-500 text-white shadow-sm"
                : "text-emerald-300 hover:text-white"
            }`}
            aria-label="English"
            aria-pressed={locale === "en"}
          >
            EN
          </button>
        </div>

        {/* Auth area */}
        {!isLoading && (
          user ? (
            <UserMenu />
          ) : (
            <div className="max-w-[40px] overflow-hidden rounded-full sm:max-w-none sm:overflow-visible sm:rounded-none">
              <div ref={btnRef} />
            </div>
          )
        )}
      </div>
    </header>
  );
}
