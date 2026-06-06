"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Card } from "@/components/ui";

const PORTAL_BASE = "https://mekarkein-online.justice.gov.il/voucher/main";

type ExtractType = "merukaz" | "histori" | "male";

export function TabooPanel({
  gush,
  chelka,
}: {
  gush: string | null;
  chelka: string | null;
}) {
  const t = useTranslations("taboo");
  const [extractType, setExtractType] = useState<ExtractType>("merukaz");

  const resolved = Boolean(gush && chelka);

  const openPortal = () => {
    // Deep-link to the official Land Registry portal, pre-filled to this parcel.
    // Extract-type selection + payment happen there (card never touches our app).
    window.open(`${PORTAL_BASE}/${gush}/${chelka}`, "_blank", "noopener,noreferrer");
  };

  return (
    <Card>
      <h3 className="mb-3 font-medium">{t("title")}</h3>

      {!resolved ? (
        <p className="text-sm text-ink/50">{t("needAddress")}</p>
      ) : (
        <div className="space-y-3">
          <p className="bidi-isolate text-sm">{t("parcel", { gush: gush!, chelka: chelka! })}</p>

          <label className="flex flex-col gap-1 text-sm">
            <span className="text-ink/70">{t("extractType")}</span>
            <select
              value={extractType}
              onChange={(e) => setExtractType(e.target.value as ExtractType)}
              className="rounded-lg border border-ink/15 px-3 py-2 outline-none focus:border-burgundy"
            >
              <option value="merukaz">{t("types.merukaz")}</option>
              <option value="histori">{t("types.histori")}</option>
              <option value="male">{t("types.male")}</option>
            </select>
          </label>

          <button
            onClick={openPortal}
            className="w-full rounded-lg bg-burgundy px-4 py-2 text-sm font-medium text-white hover:bg-burgundy/90"
          >
            {t("open")}
          </button>

          <p className="text-xs text-ink/50">{t("hint")}</p>
        </div>
      )}
    </Card>
  );
}
