import type { Metadata } from "next";
import { Frank_Ruhl_Libre, Heebo } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";

import { QueryProvider } from "@/components/query-provider";
import "./globals.css";

const heebo = Heebo({ subsets: ["hebrew"], variable: "--font-heebo" });
const frankRuhl = Frank_Ruhl_Libre({
  subsets: ["hebrew"],
  weight: ["400", "500", "700"],
  variable: "--font-frank-ruhl",
});

export const metadata: Metadata = {
  title: "הלוי · לוטטי",
  description: "בדיקות מקדמיות לעסקאות נדל\"ן",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const messages = await getMessages();
  return (
    <html lang="he" dir="rtl" className={`${heebo.variable} ${frankRuhl.variable}`}>
      <body className="font-body min-h-screen">
        <NextIntlClientProvider messages={messages} locale="he">
          <QueryProvider>{children}</QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
