"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Card, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatCurrencyILS, formatDate } from "@/lib/format";

// Automation level per step (PRD §4). Drives the badge on each step card.
const STEP_AUTOMATION: Record<number, "full" | "partial" | "ai" | "manual"> = {
  1: "full",
  2: "full",
  3: "full",
  4: "partial",
  5: "full",
  6: "full",
  7: "full",
  8: "ai",
  9: "manual",
  10: "manual",
};

function StepCard({ step }: { step: number }) {
  const t = useTranslations("case");
  const [open, setOpen] = useState(false);
  const automation = STEP_AUTOMATION[step];
  return (
    <Card className="p-0">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between p-4 text-start"
      >
        <span className="flex items-center gap-3">
          <span className="bidi-isolate flex h-7 w-7 items-center justify-center rounded-full bg-ink/5 text-sm text-ink/60">
            {step}
          </span>
          <span className="font-medium">{t(`steps.${step}` as never)}</span>
        </span>
        <span className="flex items-center gap-2">
          <span className="rounded-full bg-ink/5 px-2 py-0.5 text-xs text-ink/60">
            {t(`automation.${automation}` as never)}
          </span>
          <span className="text-xs text-ink/40">{t("stepStatus.pending")}</span>
        </span>
      </button>
      {open && (
        <div className="border-t border-ink/10 px-4 py-3 text-sm text-ink/50">
          {t("stepStatus.comingSoon")}
        </div>
      )}
    </Card>
  );
}

export function CaseDetail({ caseId }: { caseId: string }) {
  const t = useTranslations("case");
  const tNav = useTranslations("nav");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => api.getCase(caseId),
  });

  if (isLoading) return <p className="text-ink/40">…</p>;
  if (isError || !data) return <p className="text-red-600">שגיאה בטעינת התיק</p>;

  const client = data.parties[0];

  return (
    <div className="space-y-6">
      <Link href="/" className="text-sm text-ink/60 hover:text-burgundy">
        ← {tNav("backToDashboard")}
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="bidi-isolate font-display text-2xl font-bold">{data.case_number}</h1>
          <p className="text-ink/60">
            {data.property_address}, {data.property_city}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-burgundy/10 px-3 py-1 text-xs text-burgundy">
            {t("phase")}
          </span>
          <StatusBadge status={data.status} />
        </div>
      </div>

      {/* 10-segment timeline */}
      <div className="flex gap-1">
        {Array.from({ length: 10 }, (_, i) => i + 1).map((step) => (
          <div
            key={step}
            className={`h-2 flex-1 rounded-full ${
              step <= data.current_step ? "bg-burgundy" : "bg-ink/10"
            }`}
            title={`${step}`}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Step cards */}
        <div className="space-y-3 lg:col-span-2">
          {Array.from({ length: 10 }, (_, i) => i + 1).map((step) => (
            <StepCard key={step} step={step} />
          ))}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <h3 className="mb-2 font-medium">{t("redFlags")}</h3>
            <p className="text-sm text-ink/50">{t("noRedFlags")}</p>
          </Card>
          <Card>
            <h3 className="mb-3 font-medium">{t("dealDetails")}</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-ink/50">{t("blockParcel")}</dt>
                <dd className="bidi-isolate">
                  {data.block} / {data.parcel}
                  {data.sub_parcel ? ` / ${data.sub_parcel}` : ""}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-ink/50">{t("dealValue")}</dt>
                <dd className="bidi-isolate">{formatCurrencyILS(data.deal_value_ils)}</dd>
              </div>
              {client && (
                <div className="flex justify-between">
                  <dt className="text-ink/50">{t("counterparty")}</dt>
                  <dd>{data.counterparty_lawyer_name ?? "—"}</dd>
                </div>
              )}
            </dl>
          </Card>
          <Card>
            <h3 className="mb-3 font-medium">{t("recentActivity")}</h3>
            {data.activities.length === 0 ? (
              <p className="text-sm text-ink/50">{t("noActivity")}</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {data.activities.map((a) => (
                  <li key={a.id} className="flex justify-between gap-2">
                    <span>{a.description}</span>
                    <span className="bidi-isolate text-xs text-ink/40">
                      {formatDate(a.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
