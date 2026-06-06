"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui";
import { type FirmSettings, getFirmSettings } from "@/lib/firm-settings";

const PORTAL_BASE = "https://mekarkein-online.justice.gov.il/voucher/main";

type ExtractType = "merukaz" | "histori" | "male";

function CopyRow({ label, value }: { label: string; value: string }) {
  const t = useTranslations("taboo");
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable */
    }
  };
  return (
    <div className="flex items-center justify-between gap-2 text-sm">
      <span className="bidi-isolate truncate text-ink/80">
        <span className="text-ink/40">{label}: </span>
        {value}
      </span>
      <button
        onClick={copy}
        className="shrink-0 rounded-md border border-ink/15 px-2 py-0.5 text-xs hover:border-burgundy"
      >
        {copied ? t("copied") : t("copy")}
      </button>
    </div>
  );
}

export function TabooPanel({
  gush,
  chelka,
}: {
  gush: string | null;
  chelka: string | null;
}) {
  const t = useTranslations("taboo");
  const [extractType, setExtractType] = useState<ExtractType>("merukaz");
  const [firm, setFirm] = useState<FirmSettings>({ name: "", phone: "", email: "" });

  useEffect(() => {
    setFirm(getFirmSettings());
  }, []);

  const resolved = Boolean(gush && chelka);
  const hasFirm = Boolean(firm.name || firm.email || firm.phone);

  const openPortal = () => {
    // Deep-link to the official Land Registry portal, pre-filled to this parcel.
    // Requester details are copied by the lawyer; payment happens on the gov page.
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

          {/* Requester details (from firm Settings) — one-click copy onto the gov form */}
          {hasFirm ? (
            <div className="space-y-1 rounded-lg bg-ink/5 p-2">
              <p className="text-xs text-ink/50">{t("requester")}</p>
              {firm.name && <CopyRow label="שם" value={firm.name} />}
              {firm.email && <CopyRow label="@" value={firm.email} />}
              {firm.phone && <CopyRow label="☎" value={firm.phone} />}
            </div>
          ) : (
            <Link href="/settings" className="block text-xs text-burgundy hover:underline">
              {t("setFirmDetails")}
            </Link>
          )}

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
