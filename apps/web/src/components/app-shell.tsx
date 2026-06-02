"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

export function AppShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations();
  const navItems = ["dashboard", "clients", "templates", "archive", "settings"] as const;

  return (
    <div className="min-h-screen">
      <header className="border-b border-ink/10 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <Link href="/" className="font-display text-xl font-bold text-burgundy">
              {t("app.title")}
            </Link>
            <p className="text-xs text-ink/50">{t("app.subtitle")}</p>
          </div>
          <nav className="flex gap-6 text-sm">
            {navItems.map((item) => (
              <Link
                key={item}
                href={item === "dashboard" ? "/" : `/${item}`}
                className="text-ink/70 hover:text-burgundy"
              >
                {t(`nav.${item}`)}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
