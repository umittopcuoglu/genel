"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Hotel } from "lucide-react";

/**
 * Giriş ekranı — backend TASK-001 (auth) teslim edilince
 * POST /api/v1/auth/login'e bağlanacak. Şimdilik iskelet + mock yönlendirme.
 */
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError("E-posta ve şifre zorunludur.");
      return;
    }
    setLoading(true);
    try {
      // Gerçek backend (TASK-001): POST /api/v1/auth/login
      const { api } = await import("@/lib/api");
      const res = await api<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("access_token", res.access_token);
      router.push("/dashboard");
    } catch {
      // Backend erişilemiyorsa demo moduna düş (mock ekranlar yine de gezilebilir)
      localStorage.setItem("access_token", "demo");
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-xl border border-line bg-surface p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-2">
          <Hotel className="h-8 w-8 text-primary" aria-hidden />
          <h1 className="text-2xl font-semibold">HotelOps</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="mb-1 block text-sm text-text-2">
              E-posta
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-line bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm text-text-2">
              Şifre
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-line bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          {error && (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-60"
          >
            {loading ? "Giriş yapılıyor…" : "Giriş Yap"}
          </button>
        </form>
        <p className="mt-4 text-center text-xs text-text-2">
          Demo: backend kapalıyken herhangi bir bilgiyle giriş yapın.
        </p>
      </div>
    </main>
  );
}
