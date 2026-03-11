"use client";

import clsx from "clsx";
import type { CreditBalance } from "@/lib/types";
import { useLanguage } from "@/contexts/LanguageContext";

export default function CreditBadge({ credits }: { credits: CreditBalance }) {
  const { t } = useLanguage();
  const isLow = credits.total_available <= 3;
  return (
    <div
      className={clsx(
        "rounded-full px-3 py-1 text-xs font-medium",
        isLow
          ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
          : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300",
      )}
      title={t.creditBadgeTooltip(credits.daily_free_remaining, credits.paid_credits)}
    >
      {credits.total_available} {t.credits}
    </div>
  );
}
