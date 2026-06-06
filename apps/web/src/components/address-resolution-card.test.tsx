import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import messages from "../../messages/he.json";
import { AddressResolutionCard } from "./address-resolution-card";

vi.mock("@/lib/api", () => ({
  api: {
    getAddressResolution: vi.fn().mockResolvedValue(null),
    resolveAddress: vi.fn(),
    manualResolution: vi.fn(),
  },
}));

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <NextIntlClientProvider locale="he" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("AddressResolutionCard", () => {
  it("shows the not-resolved state and a resolve button when no resolution exists", async () => {
    wrap(<AddressResolutionCard caseId="abc" />);
    expect(await screen.findByText("טרם נפתר")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "פתרון כתובת לגוש/חלקה" }),
    ).toBeInTheDocument();
  });
});
