import Link from "next/link";
import {
  BarChart3,
  BedDouble,
  Boxes,
  Building2,
  Calendar,
  CreditCard,
  Fingerprint,
  Hotel,
  LayoutDashboard,
  Lightbulb,
  PartyPopper,
  ScanLine,
  Settings,
  ShieldCheck,
  Smartphone,
  Sparkles,
  UsersRound,
  UtensilsCrossed,
  Mic,
  Globe,
  Wrench,
} from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

/** Yan menü — bölümlü IA (Operasyon / Faz 3 / Faz 4). docs/03_FRONTEND_TASARIM.md §2 */
const NAV: { section: string; items: { href: string; label: string; icon: any }[] }[] = [
  {
    section: "Operasyon",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/front-office", label: "Ön Büro", icon: BedDouble },
      { href: "/reservations", label: "Rezervasyon", icon: Calendar },
      { href: "/housekeeping", label: "Housekeeping", icon: Sparkles },
      { href: "/finance", label: "Muhasebe", icon: CreditCard },
      { href: "/maintenance", label: "Bakım", icon: Wrench },
      { href: "/analytics", label: "Analitik", icon: BarChart3 },
    ],
  },
  {
    section: "Faz 3 — Olgunlaşma",
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
    section: "Faz 4 — İleri",
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
    items: [{ href: "/settings", label: "Ayarlar", icon: Settings }],
  },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 overflow-y-auto border-r border-line bg-surface md:block">
        <div className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b border-line bg-surface px-4">
          <Hotel className="h-6 w-6 text-primary" aria-hidden />
          <span className="font-semibold">HotelOps</span>
        </div>
        <nav aria-label="Ana menü" className="p-2">
          {NAV.map((group) => (
            <div key={group.section} className="mb-3">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-text-2">
                {group.section}
              </div>
              {group.items.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden />
                  {label}
                </Link>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-line bg-surface px-4">
          <input
            type="search"
            placeholder="Ara: oda, misafir, rezervasyon…  (Ctrl+K)"
            aria-label="Global arama"
            className="w-72 rounded-md border border-line bg-bg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-text-2 sm:inline">v1.0 · Faz 1-4</span>
            <ThemeToggle />
            <Link
              href="/login"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-white"
              title="Hesap"
              aria-label="Hesap menüsü"
            >
              ÜT
            </Link>
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
