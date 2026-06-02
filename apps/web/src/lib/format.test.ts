import { describe, expect, it } from "vitest";

import { formatCurrencyILS, progressLabel } from "./format";

describe("formatCurrencyILS", () => {
  it("formats shekels with the ₪ symbol and no decimals", () => {
    const out = formatCurrencyILS(3200000);
    expect(out).toContain("₪");
    expect(out).toContain("3,200,000");
  });

  it("returns a dash for null", () => {
    expect(formatCurrencyILS(null)).toBe("—");
  });
});

describe("progressLabel", () => {
  it("renders X/10", () => {
    expect(progressLabel(3)).toBe("3/10");
  });
});
