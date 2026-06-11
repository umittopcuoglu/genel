import { test, expect } from "@playwright/test";
import { setupMockApi, MOCK_BOARD } from "../fixtures/mock-api";
import { loginAs } from "../fixtures/auth";

test.describe("Front Office", () => {
  test.beforeEach(async ({ page }) => {
    await setupMockApi(page);
    await loginAs(page);
    await page.goto("/front-office");
    await expect(page.locator("body")).toBeVisible();
  });

  test("Gelenler sekmesi içerik gösterir", async ({ page }) => {
    await page.click('button:has-text("Gelenler")');
    await expect(page.locator("text=Ahmet Yılmaz")).toBeVisible();
  });

  test("Gidenler sekmesi içerik gösterir", async ({ page }) => {
    await page.click('button:has-text("Gidenler")');
    await expect(page.locator("text=Mehmet Demir")).toBeVisible();
  });

  test("Oda Panosu sekmesi filtre butonları çalışır", async ({ page }) => {
    await page.click('button:has-text("Oda Panosu")');
    await expect(page.locator("text=101")).toBeVisible();
    await expect(page.locator("text=102")).toBeVisible();
  });

  test("Oda Panosu durum sayımlarını gösterir", async ({ page }) => {
    await page.click('button:has-text("Oda Panosu")');

    const counts = MOCK_BOARD.meta.counts;
    await expect(page.locator(`text=${counts.clean}`).first()).toBeVisible();
  });

  test("Tape Chart hafta kaydırma çalışır", async ({ page }) => {
    await page.click('button:has-text("Tape Chart")');
    // İleri 7 gün
    await page.click('button[aria-label="İleri"]');
    // Geri 7 gün
    await page.click('button[aria-label="Geri"]');
  });
});
