import { test, expect } from "@playwright/test";

test.describe("Login", () => {
  test("başarısız giriş hata gösterir", async ({ page }) => {
    // Mock login failure
    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({
        status: 401,
        json: {
          error: {
            code: "INVALID_CREDENTIALS",
            message: "E-posta veya şifre hatalı.",
            details: {},
          },
        },
      })
    );

    await page.goto("/login");
    await page.fill('input[name="email"]', "wrong@test.com");
    await page.fill('input[name="password"]', "wrong123");
    await page.click('button[type="submit"]');

    await expect(page.locator("text=E-posta veya şifre hatalı")).toBeVisible();
  });

  test("başarılı giriş dashboard'a yönlendirir", async ({ page }) => {
    // Mock login success
    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({
        json: {
          access_token: "mock-jwt-token",
          refresh_token: "mock-refresh-token",
          token_type: "bearer",
        },
      })
    );

    await page.goto("/login");
    await page.fill('input[name="email"]', "admin@test.com");
    await page.fill('input[name="password"]', "Admin123!");
    await page.click('button[type="submit"]');

    // Dashboard'a yönlenmeli
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
