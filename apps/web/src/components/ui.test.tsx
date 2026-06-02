import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";

import messages from "../../messages/he.json";
import { StatusBadge } from "./ui";

function wrap(ui: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="he" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("StatusBadge", () => {
  it("renders the Hebrew label for a status", () => {
    wrap(<StatusBadge status="needs_attention" />);
    expect(screen.getByText("דורש עיון")).toBeInTheDocument();
  });
});
