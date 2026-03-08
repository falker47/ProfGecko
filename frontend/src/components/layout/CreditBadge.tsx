"use client";

import clsx from "clsx";
import type { CreditBalance } from "@/lib/types";

export default function CreditBadge({ credits }: { credits: CreditBalance }) {
  const isLow = credits.total_available <= 3;
  return (
    <div
      className={clsx(
        "rounded-full px-3 py-1 text-xs font-medium",
        isLow
          ? "bg-red-100 text-red-700"
          : "bg-emerald-100 text-emerald-700",
      )}
      title={`${credits.daily_free_remaining} gratuiti + ${credits.paid_credits} acquistati`}
    >
      {credits.total_available} crediti
    </div>
  );
}
