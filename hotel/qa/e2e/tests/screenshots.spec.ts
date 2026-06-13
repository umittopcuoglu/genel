import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

/**
 * Her sayfa için ekran görüntüsü + temel sağlık testi.
 * Backend gerekmez: (app) layout'unda auth guard yok; sayfalar API'ye
 * ulaşamayınca mock fallback (MockBanner) ile render olur.
 */

const OUT_DIR = path.join(__dirname, "..", "screenshots");

// Gezilecek rotalar — etiket : url
const ROUTES: { label: string; url: string }[] = [
  // Public
  { label: "00-login", url: "/login" },
  { label: "01-book", url: "/book" },
  { label: "02-guest-wifi", url: "/guest-wifi" },
  // Operasyon
  { label: "10-dashboard", url: "/dashboard" },
  { label: "11-front-office", url: "/front-office" },
  { label: "12-reservations", url: "/reservations" },
  { label: "13-channels", url: "/channels" },
  { label: "14-housekeeping", url: "/housekeeping" },
  { label: "15-finance", url: "/finance" },
  { label: "16-maintenance", url: "/maintenance" },
  { label: "17-analytics", url: "/analytics" },
  // İş / Finans (birleştirme kolu)
  { label: "20-payments", url: "/payments" },
  { label: "21-crm", url: "/crm" },
  { label: "22-whatsapp", url: "/whatsapp" },
  { label: "23-einvoice", url: "/einvoice" },
  { label: "24-revenue", url: "/revenue" },
  { label: "25-insights", url: "/insights" },
  // Genişleme
  { label: "30-groups", url: "/groups" },
  { label: "31-fnb", url: "/fnb" },
  { label: "32-security", url: "/security" },
  { label: "33-hr", url: "/hr" },
  { label: "34-gds", url: "/gds" },
  { label: "35-iot", url: "/iot" },
  // İleri teknoloji
  { label: "40-cv", url: "/cv" },
  { label: "41-voice", url: "/voice" },
  { label: "42-properties", url: "/properties" },
  { label: "43-mobile-checkin", url: "/mobile-checkin" },
  { label: "44-blockchain", url: "/blockchain" },
  // Ayarlar
  { label: "50-settings", url: "/settings" },
  { label: "51-settings-integrations", url: "/settings/integrations" },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

// Sahte oturum: hem access_token hem token (birleştirme kolu sayfaları token okur)
test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    const user = {
      id: "00000000-0000-0000-0000-000000000001",
      email: "superadmin@test.com",
      full_name: "Test Superadmin",
      role: "superadmin",
    };
    localStorage.setItem("access_token", "demo");
    localStorage.setItem("token", "demo");
    localStorage.setItem("user", JSON.stringify(user));
  });
});

for (const route of ROUTES) {
  test(`screenshot ${route.label} (${route.url})`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));

    // domcontentloaded + sabit bekleme: bazı sayfalar (finance/settings) backend
    // yokken sürekli retry attığından "networkidle" hiç gerçekleşmez ve goto
    // zaman aşımına uğrar. DOM + 2.5sn boyama beklemesi yeterli.
    const resp = await page.goto(route.url, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2500);

    // Ekran görüntüsü HER ZAMAN alınır (assertion'lardan önce) — teslimat bu.
    await page.screenshot({
      path: path.join(OUT_DIR, `${route.label}.png`),
      fullPage: true,
    });

    // HTTP sağlık: 200 (veya yönlendirme zinciri sonu) bekle
    expect(resp, `${route.url} yanıt vermedi`).toBeTruthy();
    expect(resp!.status(), `${route.url} HTTP ${resp!.status()}`).toBeLessThan(400);

    // İçerik render oldu mu (body boş değil)
    const bodyText = (await page.locator("body").innerText().catch(() => "")) || "";
    expect(bodyText.trim().length, `${route.url} boş render`).toBeGreaterThan(0);

    // Next.js hata ekranı (error boundary) görünmemeli
    const hasNextError = await page
      .locator("text=/Application error|Unhandled Runtime Error|This page could not be found/i")
      .count();
    expect(hasNextError, `${route.url} Next.js hata ekranı gösterdi`).toBe(0);

    // React hydration uyarıları (#418/#423/#425) kurtarılabilir — bilinen i18n/tema
    // SSR↔CSR farkı; ekranı bozmaz. Bunları ayıkla, sadece ölümcül hataları fail say.
    const HYDRATION = /Minified React error #(418|423|425)/;
    const fatal = errors.filter((e) => !HYDRATION.test(e));
    expect(fatal, `${route.url} ÖLÜMCÜL JS hataları: ${fatal.join(" | ")}`).toHaveLength(0);
  });
}
