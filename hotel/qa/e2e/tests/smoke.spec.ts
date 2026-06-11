import { test, expect } from "@playwright/test";
import { setupMockApi } from "../fixtures/mock-api";
import { loginAs } from "../fixtures/auth";

test.describe("Smoke tests", () => {
  test("dashboard sayfası yüklenir, console error yok", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    await setupMockApi(page);
    await loginAs(page);
    await page.goto("/dashboard");

    await expect(page.locator("body")).toBeVisible();
    expect(errors).toHaveLength(0);
  });
});
