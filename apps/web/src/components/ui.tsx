"use client";

import { useTranslations } from "next-intl";

import type { CaseStatus } from "@/lib/types";
import { TOTAL_STEPS } from "@/lib/format";

const STATUS_STYLES: Record<CaseStatus, string> = {
  intake_pending: "bg-gold/15 text-gold",
  intake_complete: "bg-gold/15 text-gold",
  in_progress: "bg-burgundy/10 text-burgundy",
  needs_attention: "bg-red-100 text-red-700",
  signing_scheduled: "bg-emerald-100 text-emerald-700",
  signed: "bg-emerald-100 text-emerald-700",
  archived: "bg-ink/10 text-ink/60",
};

export function StatusBadge({ status }: { status: CaseStatus }) {
  const t = useTranslations("status");
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {t(status)}
    </span>
  );
}

export function ProgressBar({ currentStep }: { currentStep: number }) {
  const pct = Math.round((currentStep / TOTAL_STEPS) * 100);
  return (
    <div className="flex items-center gap-2">
      {/* Track fills from the right in RTL automatically via flow direction. */}
      <div className="h-2 w-28 overflow-hidden rounded-full bg-ink/10">
        <div className="h-full rounded-full bg-burgundy" style={{ width: `${pct}%` }} />
      </div>
      <span className="bidi-isolate text-xs text-ink/60">
        {currentStep}/{TOTAL_STEPS}
      </span>
    </div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-ink/10 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}
