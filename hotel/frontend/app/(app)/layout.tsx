import Link from "next/link";
import {
  BarChart3,
  BedDouble,
  Calendar,
  CreditCard,
  Hotel,
  LayoutDashboard,
  Settings,
  Sparkles,
  Wrench,
} from "lucide-react";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

/** Yan menü — docs/03_FRONTEND_TASARIM.md §2 IA'nın tam kapsamı */
const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/front-office", label: "Ön Büro", icon: BedDouble },
  { href: "/reservations", label: "Rezervasyon", icon: Calendar },
  { href: "/housekeeping", label: "Housekeeping", icon: Sparkles },
  { href: "/finance", label: "Muhasebe", icon: CreditCard },
  { href: "/maintenance", label: "Bakım", icon: Wrench },
  { href: "/analytics", label: "Analitik", icon: BarChart3 },
  { href: "/settings", label: "Ayarlar", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-line bg-surface md:block">
        <div className="flex h-14 items-center gap-2 border-b border-line px-4">
          <Hotel className="h-6 w-6 text-primary" aria-hidden />
          <span className="font-semibold">HotelOps</span>
        </div>
        <nav aria-label="Ana menü" className="p-2">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </Link>
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
            <span className="hidden text-sm text-text-2 sm:inline">v1.0 · Faz 5 UI</span>
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
