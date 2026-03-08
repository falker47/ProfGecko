import { API_BASE_URL } from "./constants";
import type { AuthResponse, CreditBalance } from "./types";

export async function loginWithGoogle(
  idToken: string,
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Login fallito");
  }
  return res.json();
}

export async function getMe(token: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Sessione scaduta");
  return res.json();
}

export async function getCredits(token: string): Promise<CreditBalance> {
  const res = await fetch(`${API_BASE_URL}/api/credits`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Errore crediti");
  return res.json();
}
