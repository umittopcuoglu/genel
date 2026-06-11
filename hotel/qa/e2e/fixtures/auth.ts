import { Page } from "@playwright/test";

/**
 * Test kullanıcısı olarak giriş yapar ve token'ı localStorage'a yazar.
 * Mock API modunda çalışır (backend gerektirmez).
 */
export async function loginAs(page: Page, role: string = "superadmin") {
  const mockToken = `mock-jwt-token-for-${role}`;
  const mockUser = {
    id: "00000000-0000-0000-0000-000000000001",
    email: `${role}@test.com`,
    full_name: `Test ${role.charAt(0).toUpperCase() + role.slice(1)}`,
    role,
  };

  await page.evaluate(
    ({ token, user }) => {
      localStorage.setItem("access_token", token);
      localStorage.setItem("user", JSON.stringify(user));
    },
    { token: mockToken, user: mockUser }
  );
}
