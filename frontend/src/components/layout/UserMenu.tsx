"use client";

import { useRef, useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";
import CreditBadge from "./CreditBadge";

export default function UserMenu() {
  const { user, credits, logout } = useAuth();
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  if (!user) return null;

  return (
    <div className="relative flex items-center gap-2" ref={menuRef}>
      {credits && <CreditBadge credits={credits} />}

      <button
        onClick={() => setOpen(!open)}
        className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border-2 border-emerald-300 bg-emerald-500"
      >
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt={user.name}
            className="h-full w-full object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <span className="text-sm font-bold text-white">
            {user.name.charAt(0).toUpperCase()}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-48 max-w-[calc(100vw-2rem)] rounded-lg border border-gray-200 bg-white py-2 shadow-lg sm:w-56 dark:border-gray-700 dark:bg-gray-800">
          <div className="border-b border-gray-100 px-4 pb-2 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{user.name}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
          </div>
          {credits && (
            <div className="border-b border-gray-100 px-4 py-2 text-xs text-gray-600 dark:border-gray-700 dark:text-gray-400">
              <p>{t.freeCreditsLabel} {credits.daily_free_remaining}/{credits.daily_free_total}</p>
              <p>{t.paidCreditsLabel} {credits.paid_credits}</p>
            </div>
          )}
          <button
            onClick={() => {
              logout();
              setOpen(false);
            }}
            className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950"
          >
            {t.logout}
          </button>
        </div>
      )}
    </div>
  );
}
