"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { Locale, Translations } from "@/lib/i18n";
import { it } from "@/lib/i18n";
import { en } from "@/lib/i18n";

const LANG_KEY = "profgallade_lang";
const dictionaries: Record<Locale, Translations> = { it, en };

interface LanguageContextType {
  locale: Locale;
  t: Translations;
  setLanguage: (locale: Locale) => void;
}

const LanguageContext = createContext<LanguageContextType | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<Locale>("it");

  // Hydrate from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(LANG_KEY);
    if (stored === "en" || stored === "it") {
      setLocale(stored);
    }
  }, []);

  // Update <html lang="..."> and localStorage when locale changes
  useEffect(() => {
    document.documentElement.lang = locale;
    localStorage.setItem(LANG_KEY, locale);
  }, [locale]);

  const setLanguage = useCallback((l: Locale) => {
    setLocale(l);
  }, []);

  return (
    <LanguageContext.Provider
      value={{ locale, t: dictionaries[locale], setLanguage }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
