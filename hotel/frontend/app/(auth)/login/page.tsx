"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Hotel, KeyRound, Mail, Sparkles } from "lucide-react";

/**
 * Giriş ekranı — "Grand Hotel" split-screen tasarım.
 * Sol: koyu lacivert marka paneli (altın detaylar, yüzen rozetler).
 * Sağ: zarif form, odakta altın halka, mikro-animasyonlar.
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
    <main className="flex min-h-screen">
      {/* Sol — marka paneli */}
      <section
        className="relative hidden flex-1 flex-col justify-between overflow-hidden p-12 lg:flex"
        style={{ background: "linear-gradient(160deg, #101c32 0%, #17335c 60%, #1d447c 100%)" }}
      >
        {/* Dekoratif altın halkalar */}
        <div className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full border border-[#c0984a]/20" />
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full border border-[#c0984a]/15" />
        <div className="pointer-events-none absolute -bottom-40 -left-24 h-[28rem] w-[28rem] rounded-full bg-[#c0984a]/[0.06] blur-2xl" />

        <div className="page-enter flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#c8a35a] to-[#a37e35] shadow-xl shadow-black/40">
            <Hotel className="h-6 w-6 text-white" aria-hidden />
          </span>
          <span>
            <span className="block font-display text-2xl font-semibold tracking-wide text-white">HotelOps</span>
            <span className="block text-[11px] uppercase tracking-[0.25em] text-[#c0984a]">Grand Suite PMS</span>
          </span>
        </div>

        <div className="stagger max-w-md">
          <h1 className="font-display text-4xl font-semibold leading-snug text-white">
            Otelinizi sanat eseri gibi yönetin.
          </h1>
          <p className="mt-4 text-[15px] leading-relaxed text-white/60">
            Ön bürodan housekeeping&apos;e, gelir yönetiminden misafir deneyimine —
            10 modül ve AI ajanları tek çatı altında.
          </p>
          <div className="mt-8 flex flex-wrap gap-2">
            {["FrontDesk AI", "RevenueIQ", "GuestAI", "CleanOps"].map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/80 backdrop-blur-sm"
              >
                <Sparkles className="h-3 w-3 text-[#d6b26a]" aria-hidden />
                {tag}
              </span>
            ))}
          </div>
        </div>

        <p className="text-xs text-white/35">© 2026 HotelOps · AI destekli otel yönetim platformu</p>
      </section>

      {/* Sağ — form */}
      <section className="flex flex-1 items-center justify-center bg-bg p-6">
        <div className="page-enter w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2">
              <Hotel className="h-8 w-8 text-accent" aria-hidden />
              <h1 className="font-display text-2xl font-semibold">HotelOps</h1>
            </div>
          </div>

          <h2 className="font-display text-[28px] font-semibold tracking-wide">Hoş geldiniz</h2>
          <p className="mt-1 text-sm text-text-2">Devam etmek için hesabınıza giriş yapın.</p>
          <div className="mt-4 h-[2px] w-14 rounded-full bg-gradient-to-r from-accent to-transparent" />

          <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="mb-1.5 block text-[13px] font-medium text-text-2">
                E-posta
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-2/70" aria-hidden />
                <input
                  id="email"
                  type="email"
                  autoComplete="username"
                  placeholder="ornek@otel.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-line bg-surface py-2.5 pl-10 pr-3 text-sm outline-none transition-all duration-200 focus:border-accent/60 focus:shadow-[0_0_0_3px_rgb(var(--color-accent)/0.15)]"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-[13px] font-medium text-text-2">
                Şifre
              </label>
              <div className="relative">
                <KeyRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-2/70" aria-hidden />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-line bg-surface py-2.5 pl-10 pr-3 text-sm outline-none transition-all duration-200 focus:border-accent/60 focus:shadow-[0_0_0_3px_rgb(var(--color-accent)/0.15)]"
                />
              </div>
            </div>
            {error && (
              <p role="alert" className="rounded-lg border border-danger/25 bg-danger/[0.07] px-3 py-2 text-sm text-danger">
                {error}
              </p>
            )}
            <button type="submit" disabled={loading} className="btn-gold w-full disabled:opacity-60">
              {loading ? "Giriş yapılıyor…" : "Giriş Yap"}
            </button>
          </form>
          <p className="mt-5 text-center text-xs text-text-2">
            Demo: backend kapalıyken herhangi bir bilgiyle giriş yapın.
          </p>
        </div>
      </section>
    </main>
  );
}
