import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: process.env.CI ? "http://localhost:3000" : "http://localhost:3000",
    screenshot: "only-on-failure",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium-light",
      use: { ...devices["Desktop Chrome"], colorScheme: "light" },
    },
    {
      name: "chromium-dark",
      use: { ...devices["Desktop Chrome"], colorScheme: "dark" },
    },
    {
      name: "mobile-light",
      use: { ...devices["iPhone 13"], colorScheme: "light" },
    },
    {
      name: "mobile-dark",
      use: { ...devices["iPhone 13"], colorScheme: "dark" },
    },
  ],
  webServer: process.env.CI
    ? {
        command: "cd ../../frontend && npx next start -p 3000",
        port: 3000,
        reuseExistingServer: true,
      }
    : undefined,
});
