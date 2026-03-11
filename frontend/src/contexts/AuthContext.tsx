"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { getCredits, getMe, loginWithGoogle } from "@/lib/auth-api";
import { GOOGLE_CLIENT_ID } from "@/lib/constants";
import type { CreditBalance, User } from "@/lib/types";
import { useLanguage } from "@/contexts/LanguageContext";

/* ------------------------------------------------------------------ */
/*  Google Identity Services type declarations                        */
/* ------------------------------------------------------------------ */

interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleAccountsId {
  initialize: (config: {
    client_id: string;
    callback: (resp: GoogleCredentialResponse) => void;
    auto_select?: boolean;
  }) => void;
  prompt: () => void;
  renderButton: (
    el: HTMLElement,
    config: {
      theme?: string;
      size?: string;
      text?: string;
      locale?: string;
      width?: number;
    },
  ) => void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } };
  }
}

/* ------------------------------------------------------------------ */
/*  Context                                                           */
/* ------------------------------------------------------------------ */

const TOKEN_KEY = "profgallade_jwt";

interface AuthContextType {
  user: User | null;
  credits: CreditBalance | null;
  token: string | null;
  isLoading: boolean;
  login: () => void;
  logout: () => void;
  refreshCredits: () => Promise<void>;
  /** Render the Google Sign-In button into a DOM element. */
  renderGoogleButton: (el: HTMLElement) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [credits, setCredits] = useState<CreditBalance | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [gisReady, setGisReady] = useState(false);
  const { t } = useLanguage();

  // --- Handle Google login response ---
  const handleGoogleResponse = useCallback(
    async (response: GoogleCredentialResponse) => {
      try {
        const auth = await loginWithGoogle(response.credential);
        setToken(auth.access_token);
        setUser(auth.user);
        setCredits(auth.credits);
        localStorage.setItem(TOKEN_KEY, auth.access_token);
      } catch (err) {
        console.error("Login failed:", err);
      }
    },
    [],
  );

  // --- Initialize GIS once the script loads ---
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      setIsLoading(false);
      return;
    }

    function tryInit() {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
        });
        setGisReady(true);
        return true;
      }
      return false;
    }

    // Script might already be loaded
    if (tryInit()) {
      // already set up
    } else {
      // Wait for script to load
      const interval = setInterval(() => {
        if (tryInit()) clearInterval(interval);
      }, 200);
      // Give up after 10 seconds
      setTimeout(() => clearInterval(interval), 10000);
    }
  }, [handleGoogleResponse]);

  // --- Restore session from localStorage ---
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (!savedToken) {
      setIsLoading(false);
      return;
    }

    getMe(savedToken)
      .then((auth) => {
        setToken(auth.access_token);
        setUser(auth.user);
        setCredits(auth.credits);
        localStorage.setItem(TOKEN_KEY, auth.access_token);
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => setIsLoading(false));
  }, []);

  // --- Actions ---

  const login = useCallback(() => {
    if (gisReady && window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
    }
  }, [gisReady]);

  const logout = useCallback(() => {
    setUser(null);
    setCredits(null);
    setToken(null);
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  const refreshCredits = useCallback(async () => {
    if (!token) return;
    try {
      const bal = await getCredits(token);
      setCredits(bal);
    } catch {
      // silently fail
    }
  }, [token]);

  const renderGoogleButton = useCallback(
    (el: HTMLElement) => {
      if (gisReady && window.google?.accounts?.id) {
        window.google.accounts.id.renderButton(el, {
          theme: "outline",
          size: "medium",
          text: "signin_with",
          locale: t.googleButtonLocale,
        });
      }
    },
    [gisReady, t.googleButtonLocale],
  );

  // --- Update credits from SSE done event ---
  useEffect(() => {
    function handleCreditsUpdate(e: CustomEvent<CreditBalance>) {
      setCredits(e.detail);
    }
    window.addEventListener(
      "credits-updated",
      handleCreditsUpdate as EventListener,
    );
    return () =>
      window.removeEventListener(
        "credits-updated",
        handleCreditsUpdate as EventListener,
      );
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        credits,
        token,
        isLoading,
        login,
        logout,
        refreshCredits,
        renderGoogleButton,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
