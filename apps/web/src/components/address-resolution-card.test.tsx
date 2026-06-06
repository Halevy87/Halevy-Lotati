import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import messages from "../../messages/he.json";
import { api } from "@/lib/api";
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

  it("shows the resolved gush/chelka and hides the manual form when auto_resolved", async () => {
    vi.mocked(api.getAddressResolution).mockResolvedValueOnce({
      id: "1",
      case_id: "abc",
      city: "בת ים",
      street: "בר יהודה",
      number: "33",
      apartment_number_claimed: null,
      status: "auto_resolved",
      resolved_gush: "7136",
      resolved_chelka: "142",
      resolved_tat_chelka: null,
      coordinates: null,
      method: "rest",
      resolution_time_ms: 10,
      resolved_at: "2026-06-07T00:00:00Z",
    });
    wrap(<AddressResolutionCard caseId="abc" />);
    expect(await screen.findByText("גוש 7136 / חלקה 142")).toBeInTheDocument();
    expect(screen.queryByText("הזנה ידנית")).not.toBeInTheDocument();
  });
});
