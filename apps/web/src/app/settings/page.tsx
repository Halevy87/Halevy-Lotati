"use client";

import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { getFirmSettings, saveFirmSettings } from "@/lib/firm-settings";

export default function SettingsPage() {
  const t = useTranslations("settings");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const s = getFirmSettings();
    setName(s.name);
    setPhone(s.phone);
    setEmail(s.email);
  }, []);

  const onSave = () => {
    saveFirmSettings({ name, phone, email });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const field = (label: string, value: string, set: (v: string) => void, type = "text") => (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-ink/70">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => set(e.target.value)}
        className="rounded-lg border border-ink/15 px-3 py-2 outline-none focus:border-burgundy"
      />
    </label>
  );

  return (
    <AppShell>
      <div className="space-y-6">
        <h1 className="font-display text-2xl font-bold">{t("title")}</h1>
        <Card className="max-w-xl">
          <h3 className="mb-1 font-medium">{t("firmDetailsTitle")}</h3>
          <p className="mb-4 text-sm text-ink/50">{t("firmDetailsHint")}</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {field(t("name"), name, setName)}
            {field(t("phone"), phone, setPhone)}
            {field(t("email"), email, setEmail, "email")}
          </div>
          <div className="mt-5 flex items-center gap-3">
            <button
              onClick={onSave}
              className="rounded-lg bg-burgundy px-5 py-2 text-sm font-medium text-white hover:bg-burgundy/90"
            >
              {t("save")}
            </button>
            {saved && <span className="text-sm text-emerald-700">{t("saved")}</span>}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
