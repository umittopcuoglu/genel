"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BedDouble,
  Building2,
  Calendar,
  CreditCard,
  Fingerprint,
  Hotel,
  LayoutDashboard,
  Lightbulb,
  PartyPopper,
  Plug,
  ScanLine,
  Settings,
  Share2,
  ShieldCheck,
  Smartphone,
  Sparkles,
  UsersRound,
  UtensilsCrossed,
  Mic,
  Globe,
  Wrench,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";

/** Yan menü — bölümlü IA (Operasyon / Faz 3 / Faz 4). "Grand Hotel" koyu lacivert tema. */
const NAV: { section: string; sectionKey: string; items: { href: string; labelKey: string; icon: any }[] }[] = [
  {
    section: "Operasyon",
    sectionKey: "Operation",
    items: [
      { href: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard },
      { href: "/front-office", labelKey: "nav.frontOffice", icon: BedDouble },
      { href: "/reservations", labelKey: "nav.reservations", icon: Calendar },
      { href: "/channels", labelKey: "nav.channels", icon: Share2 },
      { href: "/book", labelKey: "nav.guestWifi", icon: Globe },
      { href: "/housekeeping", labelKey: "nav.housekeeping", icon: Sparkles },
      { href: "/finance", labelKey: "nav.finance", icon: CreditCard },
      { href: "/maintenance", labelKey: "nav.maintenance", icon: Wrench },
      { href: "/analytics", labelKey: "nav.analytics", icon: BarChart3 },
    ],
  },
  {
    section: "Genişleme",
    sectionKey: "Expansion",
    items: [
      { href: "/groups", labelKey: "nav.groups", icon: PartyPopper },
      { href: "/fnb", labelKey: "nav.fnb", icon: UtensilsCrossed },
      { href: "/security", labelKey: "nav.security", icon: ShieldCheck },
      { href: "/hr", labelKey: "nav.hr", icon: UsersRound },
      { href: "/gds", labelKey: "nav.gds", icon: Globe },
      { href: "/iot", labelKey: "nav.iot", icon: Lightbulb },
    ],
  },
  {
    section: "İleri Teknoloji",
    sectionKey: "Advanced",
    items: [
      { href: "/cv", labelKey: "nav.cv", icon: ScanLine },
      { href: "/voice", labelKey: "nav.voice", icon: Mic },
      { href: "/properties", labelKey: "nav.properties", icon: Building2 },
      { href: "/mobile-checkin", labelKey: "nav.mobileCheckin", icon: Smartphone },
      { href: "/blockchain", labelKey: "nav.blockchain", icon: Fingerprint },
    ],
  },
  {
    section: "Sistem",
    sectionKey: "System",
    items: [
      { href: "/settings", labelKey: "nav.settings", icon: Settings },
      { href: "/settings/integrations", labelKey: "nav.guestWifi", icon: Plug },
    ],
  },
];

const SECTION_LABELS: Record<string, { tr: string; en: string }> = {
  Operation: { tr: "Operasyon", en: "Operations" },
  Expansion: { tr: "Genişleme", en: "Expansion" },
  Advanced: { tr: "İleri Teknoloji", en: "Advanced Technology" },
  System: { tr: "Sistem", en: "System" },
};

export function Sidebar() {
  const pathname = usePathname();
  const { t, language } = useTranslation();

  return (
    <aside className="sidebar-dark hidden w-[264px] shrink-0 flex-col overflow-y-auto md:flex"
      style={{ background: "rgb(var(--sidebar-bg))" }}>
      {/* Marka alanı */}
      <div className="sticky top-0 z-10 px-5 pb-4 pt-6" style={{ background: "rgb(var(--sidebar-bg))" }}>
        <Link href="/dashboard" className="group flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#c8a35a] to-[#a37e35] shadow-lg shadow-black/30 transition-transform duration-300 group-hover:scale-105 group-hover:rotate-3">
            <Hotel className="h-5 w-5 text-white" aria-hidden />
          </span>
          <span className="leading-tight">
            <span className="block font-display text-lg font-semibold tracking-wide text-white">HotelOps</span>
            <span className="block text-[10px] uppercase tracking-[0.22em] text-[#c0984a]">Grand Suite PMS</span>
          </span>
        </Link>
        <div className="gold-line mt-5" />
      </div>

      <nav aria-label={language === "tr" ? "Ana menü" : "Main menu"} className="flex-1 px-3 pb-6">
        {NAV.map((group) => (
          <div key={group.sectionKey} className="mb-4">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
              {SECTION_LABELS[group.sectionKey]?.[language] || group.section}
            </div>
            <div className="space-y-0.5">
              {group.items.map(({ href, labelKey, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(href + "/");
                return (
                  <Link key={href} href={href} className={`nav-item ${active ? "active" : ""}`}>
                    <Icon
                      className={`h-4 w-4 shrink-0 transition-colors duration-200 ${active ? "text-[#d6b26a]" : ""}`}
                      aria-hidden
                    />
                    {t(labelKey)}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Alt bilgi */}
      <div className="px-5 pb-5">
        <div className="gold-line mb-4" />
        <p className="text-[11px] leading-relaxed text-white/35">
          v1.0 · {language === "tr" ? "Faz 1–4" : "Phase 1–4"}
          <br />
          {language === "tr" ? "AI destekli otel yönetimi" : "AI-powered hotel management"}
        </p>
      </div>
    </aside>
  );
}
