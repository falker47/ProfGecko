"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function LoginPrompt() {
  const { renderGoogleButton } = useAuth();
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (btnRef.current) {
      renderGoogleButton(btnRef.current);
    }
  }, [renderGoogleButton]);

  return (
    <div className="mx-4 mb-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-center">
      <p className="mb-2 text-sm text-emerald-800">
        Ti piace Prof. Gallade? Accedi per ottenere{" "}
        <strong>10 crediti gratuiti</strong> ogni giorno!
      </p>
      <div className="flex justify-center">
        <div ref={btnRef} />
      </div>
    </div>
  );
}
