"use client";

import { useState, useEffect, useCallback } from "react";
import AdminLogin from "@/components/admin/AdminLogin";
import AdminDashboard from "@/components/admin/AdminDashboard";

const ADMIN_SECRET_KEY = "profgecko_admin_secret";

export default function AdminPage() {
  const [secret, setSecret] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(ADMIN_SECRET_KEY);
    if (stored) setSecret(stored);
    setReady(true);
  }, []);

  const handleLogin = useCallback((s: string) => {
    sessionStorage.setItem(ADMIN_SECRET_KEY, s);
    setSecret(s);
  }, []);

  const handleAuthFailed = useCallback(() => {
    sessionStorage.removeItem(ADMIN_SECRET_KEY);
    setSecret(null);
  }, []);

  // Evita flash del login se il secret è in sessionStorage
  if (!ready) return null;

  if (!secret) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  return (
    <AdminDashboard secret={secret} onAuthFailed={handleAuthFailed} />
  );
}
