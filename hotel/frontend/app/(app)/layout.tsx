"use client";

import Link from "next/link";
import { Search } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTranslation } from "@/lib/i18n";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { t, language } = useTranslation();

  return (
    <div className="flex min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-white focus:shadow-lg"
      >
        {language === "tr" ? "İçeriğe atla" : "Skip to content"}
      </a>
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Cam efektli üst bar */}
        <header className="glass sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line px-6">
          <div className="relative w-80 max-w-full">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-2" aria-hidden />
            <input
              type="search"
              placeholder={language === "tr" ? "Oda, misafir, rezervasyon ara…" : "Search room, guest, reservation…"}
              aria-label={language === "tr" ? "Global arama" : "Global search"}
              className="w-full rounded-xl border border-line bg-bg/60 py-2 pl-9 pr-12 text-sm outline-none transition-all duration-200 focus:border-accent/60 focus:bg-surface focus:shadow-[0_0_0_3px_rgb(var(--color-accent)/0.15)]"
            />
            <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-line bg-surface px-1.5 py-0.5 text-[10px] font-medium text-text-2">
              Ctrl K
            </kbd>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-medium text-accent sm:inline">
              v1.0 · {language === "tr" ? "Faz" : "Phase"} 1–4
            </span>
            <LanguageSwitcher />
            <ThemeToggle />
            <Link
              href="/login"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary to-[#0d1f3c] text-xs font-semibold text-white ring-2 ring-transparent transition-all duration-200 hover:ring-accent/50 hover:scale-105"
              title={language === "tr" ? "Hesap" : "Account"}
              aria-label={language === "tr" ? "Hesap menüsü" : "Account menu"}
            >
              ÜT
            </Link>
          </div>
        </header>
        <main id="main-content" className="flex-1 p-6 lg:p-8" tabIndex={-1}>{children}</main>
      </div>
    </div>
  );
}
