import { defineConfig, devices } from "@playwright/test";

// PRD §0 browser matrix: Chrome, Safari, mobile Safari iOS, Android Chrome.
export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  use: { baseURL: "http://localhost:3000" },
  projects: [
    { name: "Desktop Chrome", use: { ...devices["Desktop Chrome"] } },
    { name: "Desktop Safari", use: { ...devices["Desktop Safari"] } },
    { name: "Mobile Safari", use: { ...devices["iPhone 14"] } },
    { name: "Android Chrome", use: { ...devices["Pixel 7"] } },
  ],
});
