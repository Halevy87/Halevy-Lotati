"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import { NewCaseModal } from "@/components/new-case-modal";
import { Card, ProgressBar, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import type { CaseListItem } from "@/lib/types";

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <p className="text-sm text-ink/60">{label}</p>
      <p className="bidi-isolate mt-2 font-display text-3xl font-bold text-ink">{value}</p>
    </Card>
  );
}

export function Dashboard() {
  const t = useTranslations("dashboard");
  const [modalOpen, setModalOpen] = useState(false);
  const { data, isLoading, isError } = useQuery({
    queryKey: ["cases"],
    queryFn: api.listCases,
  });

  const items: CaseListItem[] = useMemo(() => data?.items ?? [], [data]);
  const kpis = useMemo(
    () => ({
      active: items.filter((c) => !["signed", "archived"].includes(c.status)).length,
      checks: 0,
      attention: items.filter((c) => c.status === "needs_attention").length,
      signings: items.filter((c) => c.status === "signing_scheduled").length,
    }),
    [items],
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold">{t("title")}</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-burgundy px-4 py-2 text-sm font-medium text-white hover:bg-burgundy/90"
        >
          + {t("newCase")}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label={t("kpi.activeCases")} value={kpis.active} />
        <Kpi label={t("kpi.checksThisWeek")} value={kpis.checks} />
        <Kpi label={t("kpi.needsAttention")} value={kpis.attention} />
        <Kpi label={t("kpi.signingsThisWeek")} value={kpis.signings} />
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full text-start text-sm">
          <thead className="border-b border-ink/10 text-ink/60">
            <tr>
              <th className="px-5 py-3 text-start font-medium">{t("table.caseNumber")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("table.address")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("table.status")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("table.progress")}</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-ink/40">
                  …
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-red-600">
                  שגיאה בטעינת התיקים
                </td>
              </tr>
            )}
            {!isLoading && !isError && items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-ink/40">
                  {t("table.empty")}
                </td>
              </tr>
            )}
            {items.map((c) => (
              <tr key={c.id} className="border-b border-ink/5 hover:bg-paper">
                <td className="px-5 py-3">
                  <Link href={`/cases/${c.id}`} className="bidi-isolate text-burgundy hover:underline">
                    {c.case_number}
                  </Link>
                </td>
                <td className="px-5 py-3">
                  {c.property_address}, {c.property_city}
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={c.status} />
                </td>
                <td className="px-5 py-3">
                  <ProgressBar currentStep={c.current_step} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {modalOpen && <NewCaseModal onClose={() => setModalOpen(false)} />}
    </div>
  );
}
