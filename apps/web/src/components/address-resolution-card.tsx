"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { Card } from "@/components/ui";
import { api } from "@/lib/api";

export function AddressResolutionCard({ caseId }: { caseId: string }) {
  const t = useTranslations("addressResolution");
  const queryClient = useQueryClient();
  const [gush, setGush] = useState("");
  const [chelka, setChelka] = useState("");
  const [tatChelka, setTatChelka] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["address-resolution", caseId],
    queryFn: () => api.getAddressResolution(caseId),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["address-resolution", caseId] });
    queryClient.invalidateQueries({ queryKey: ["case", caseId] });
  };

  const resolveMutation = useMutation({
    mutationFn: () => api.resolveAddress(caseId),
    onSuccess: invalidate,
  });

  const manualMutation = useMutation({
    mutationFn: () => api.manualResolution(caseId, { gush, chelka, tat_chelka: tatChelka || null }),
    onSuccess: () => {
      invalidate();
      setGush("");
      setChelka("");
      setTatChelka("");
    },
  });

  const resolved = data && (data.status === "auto_resolved" || data.status === "manual_entry");
  const showManual = !resolved;

  return (
    <Card>
      <h3 className="mb-3 font-medium">{t("title")}</h3>

      {isLoading ? (
        <p className="text-sm text-ink/40">…</p>
      ) : resolved ? (
        <p className="bidi-isolate text-sm">
          {t("resolved", { gush: data!.resolved_gush ?? "", chelka: data!.resolved_chelka ?? "" })}
          {data!.resolved_tat_chelka ? ` / ${data!.resolved_tat_chelka}` : ""}
        </p>
      ) : (
        <p className="text-sm text-ink/50">{t("notResolved")}</p>
      )}

      {(data?.status === "failed" || resolveMutation.isError || manualMutation.isError) && (
        <p className="mt-1 text-xs text-red-600">{t("failed")}</p>
      )}
      {data?.status === "multi_candidate" && (
        <p className="mt-1 text-xs text-gold">{t("multiCandidate")}</p>
      )}

      {!resolved && (
        <button
          onClick={() => resolveMutation.mutate()}
          disabled={resolveMutation.isPending}
          className="mt-3 rounded-lg bg-burgundy px-4 py-2 text-sm font-medium text-white hover:bg-burgundy/90 disabled:opacity-50"
        >
          {resolveMutation.isPending ? t("resolving") : t("resolveButton")}
        </button>
      )}

      {showManual && (
        <div className="mt-4 border-t border-ink/10 pt-3">
          <h4 className="mb-2 text-sm font-medium">{t("manualTitle")}</h4>
          <div className="grid grid-cols-3 gap-2">
            <input
              aria-label={t("gush")}
              placeholder={t("gush")}
              value={gush}
              onChange={(e) => setGush(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
            <input
              aria-label={t("chelka")}
              placeholder={t("chelka")}
              value={chelka}
              onChange={(e) => setChelka(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
            <input
              aria-label={t("tatChelka")}
              placeholder={t("tatChelka")}
              value={tatChelka}
              onChange={(e) => setTatChelka(e.target.value)}
              className="rounded-lg border border-ink/15 px-2 py-1 text-sm outline-none focus:border-burgundy"
            />
          </div>
          <button
            onClick={() => manualMutation.mutate()}
            disabled={!gush || !chelka || manualMutation.isPending}
            className="mt-2 rounded-lg border border-ink/15 px-4 py-1.5 text-sm hover:border-burgundy disabled:opacity-50"
          >
            {t("save")}
          </button>
        </div>
      )}
    </Card>
  );
}
