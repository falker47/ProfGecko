"use client";

import { useEffect, useRef } from "react";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import UserMenu from "./UserMenu";

export default function Header() {
  const { user, isLoading, renderGoogleButton } = useAuth();
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user && !isLoading && btnRef.current) {
      renderGoogleButton(btnRef.current);
    }
  }, [user, isLoading, renderGoogleButton]);

  return (
    <header className="bg-emerald-700 text-white shadow-md">
      <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3">
        <Image
          src="/profgallade-avatar.jpg"
          alt="Prof. Gallade"
          width={40}
          height={40}
          className="h-10 w-10 rounded-full ring-2 ring-emerald-400"
        />
        <div className="flex-1">
          <h1 className="text-lg font-bold leading-tight">Prof. Gallade</h1>
          <p className="text-xs text-emerald-200">Esperto Pokemon</p>
        </div>

        {/* Auth area */}
        {!isLoading && (
          user ? (
            <UserMenu />
          ) : (
            <div ref={btnRef} />
          )
        )}
      </div>
    </header>
  );
}
