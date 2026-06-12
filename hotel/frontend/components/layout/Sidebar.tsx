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
  Users,
  MessageCircle,
} from "lucide-react";

/** Yan menü — bölümlü IA (Operasyon / Faz 3 / Faz 4). "Grand Hotel" koyu lacivert tema. */
const NAV: { section: string; items: { href: string; label: string; icon: any }[] }[] = [
  {
    section: "Operasyon",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/front-office", label: "Ön Büro", icon: BedDouble },
      { href: "/reservations", label: "Rezervasyon", icon: Calendar },
      { href: "/channels", label: "Channel Manager", icon: Share2 },
      { href: "/book", label: "Booking Engine", icon: Globe },
      { href: "/housekeeping", label: "Housekeeping", icon: Sparkles },
      { href: "/finance", label: "Muhasebe", icon: CreditCard },
      { href: "/payments", label: "Ödeme / POS", icon: CreditCard },
      { href: "/crm", label: "CRM / Misafir 360", icon: Users },
      { href: "/whatsapp", label: "WhatsApp", icon: MessageCircle },
      { href: "/maintenance", label: "Bakım", icon: Wrench },
      { href: "/analytics", label: "Analitik", icon: BarChart3 },
    ],
  },
  {
    section: "Genişleme",
    items: [
      { href: "/groups", label: "Gruplar & Etkinlik", icon: PartyPopper },
      { href: "/fnb", label: "F&B / POS", icon: UtensilsCrossed },
      { href: "/security", label: "Güvenlik & KVKK", icon: ShieldCheck },
      { href: "/hr", label: "İK & Vardiya", icon: UsersRound },
      { href: "/gds", label: "GDS", icon: Globe },
      { href: "/iot", label: "IoT / Akıllı Oda", icon: Lightbulb },
    ],
  },
  {
    section: "İleri Teknoloji",
    items: [
      { href: "/cv", label: "Görüntü Denetimi", icon: ScanLine },
      { href: "/voice", label: "Sesli Kontrol", icon: Mic },
      { href: "/properties", label: "Çoklu Tesis", icon: Building2 },
      { href: "/mobile-checkin", label: "Mobil Check-in", icon: Smartphone },
      { href: "/blockchain", label: "Blockchain Kimlik", icon: Fingerprint },
    ],
  },
  {
    section: "Sistem",
    items: [
      { href: "/settings", label: "Ayarlar", icon: Settings },
      { href: "/settings/integrations", label: "Entegrasyonlar", icon: Plug },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

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

      <nav aria-label="Ana menü" className="flex-1 px-3 pb-6">
        {NAV.map((group) => (
          <div key={group.section} className="mb-4">
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/30">
              {group.section}
            </div>
            <div className="space-y-0.5">
              {group.items.map(({ href, label, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(href + "/");
                return (
                  <Link key={href} href={href} className={`nav-item ${active ? "active" : ""}`}>
                    <Icon
                      className={`h-4 w-4 shrink-0 transition-colors duration-200 ${active ? "text-[#d6b26a]" : ""}`}
                      aria-hidden
                    />
                    {label}
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
          v1.0 · Faz 1–4
          <br />
          AI destekli otel yönetimi
        </p>
      </div>
    </aside>
  );
}
