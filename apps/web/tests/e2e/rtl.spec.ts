import { expect, test } from "@playwright/test";

// Validates the non-negotiable RTL/Hebrew foundation (PRD §0) across the browser matrix.
test("dashboard renders RTL Hebrew with no horizontal overflow", async ({ page }) => {
  await page.goto("/");

  // dir=rtl / lang=he on the root element
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "he");

  // Hebrew brand + dashboard heading present
  await expect(page.getByText("לוח עבודה").first()).toBeVisible();

  // No horizontal overflow at the current viewport
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(overflow).toBe(false);
});
