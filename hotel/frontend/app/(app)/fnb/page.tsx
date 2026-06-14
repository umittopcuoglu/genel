"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_OUTLETS, MOCK_CHECKS, MOCK_MENU } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

// Backend (TASK-016) → ekran satır şekli normalizasyonu.
type OutletRow = { id: string; name: string; type: string; open: boolean; todaySales: number };
type MenuRow = { id: string; name: string; category: string; price: number; cost: number; popular: boolean };

function normalizeOutlets(raw: any[]): OutletRow[] {
  return raw.map((o) => ({
    id: String(o.id),
    name: o.name,
    type: o.outlet_type ?? o.type ?? "—",
    open: o.is_open ?? o.open ?? false,
    todaySales: o.todaySales ?? 0,
  }));
}

function normalizeMenu(raw: any[]): MenuRow[] {
  return raw.map((m) => ({
    id: String(m.id),
    name: m.name,
    category: m.category,
    price: Number(m.price ?? 0),
    cost: Number(m.cost ?? 0),
    popular: m.popular ?? false,
  }));
}

export default function FnbPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"outlets" | "checks" | "menu">("outlets");

  const { data: outletsRaw, usingFallback: outletsFallback } = useApiData<any[]>({
    path: "/api/v1/fnb/outlets",
    fallback: MOCK_OUTLETS,
  });
  const { data: menuRaw, usingFallback: menuFallback } = useApiData<any[]>({
    path: "/api/v1/fnb/menu-items",
    fallback: MOCK_MENU,
  });

  const outlets = outletsFallback ? MOCK_OUTLETS : normalizeOutlets(outletsRaw);
  const menu = menuFallback ? MOCK_MENU : normalizeMenu(menuRaw);
  // Adisyon listesi için backend toplu uç sağlamıyor (yalnızca GET /checks/{id}) → mock kalır.
  const checks = MOCK_CHECKS;
  const usingFallback = outletsFallback || menuFallback;

  const todayTotal = outlets.reduce((s, o) => s + (o.todaySales ?? 0), 0);

  const tabs = [
    { id: "outlets", label: t('fnb.outlets') },
    { id: "checks", label: "Adisyonlar" },
    { id: "menu", label: "Menü" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t('fnb.title')} subtitle={`${outlets.length} satış noktası · dış POS entegrasyonu (mock)${usingFallback ? " · demo veri" : ""}`} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Bugünkü F&B Geliri" value={tl(todayTotal)} tone="success" />
        <StatCard label="Açık Adisyon" value={String(checks.filter((c) => c.status === "open").length)} />
        <StatCard label={t('fnb.outlets')} value={String(outlets.length)} />
        <StatCard label="Menü Kalemi" value={String(menu.length)} />
      </div>

      <AIPanel
        agent="ChefIQ AI"
        suggestion="Grilled seabass demand up 35% on weekends; recommend +18kg stock. Tiramisu has high margin but low popularity — promote on menu."
        rationale="Historical sales + profit/popularity matrix"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {tabs.map(({ id, label }) => (
            <button key={id} role="tab" aria-selected={tab === id as any} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "outlets" && (
        <SimpleTable rows={outlets} columns={[
          { key: "name", header: t('fnb.outletName') },
          { key: "type", header: t('fnb.category') },
          { key: "open", header: t('common.status'), render: (o) => (o.open ? <Badge tone="success">Açık</Badge> : <Badge>Kapalı</Badge>) },
          { key: "todaySales", header: "Bugünkü Satış", align: "right", render: (o) => tl(o.todaySales ?? 0) },
        ]} />
      )}
      {tab === "checks" && (
        <SimpleTable rows={checks} columns={[
          { key: "outlet", header: t('fnb.outlets') },
          { key: "table", header: "Masa" },
          { key: "room", header: "Oda", render: (c) => c.room ?? "—" },
          { key: "items", header: t('fnb.quantity'), align: "right" },
          { key: "total", header: t('fnb.total'), align: "right", render: (c) => tl(c.total) },
          { key: "status", header: t('common.status'), render: (c) => <Badge tone={c.status === "open" ? "info" : "neutral"}>{c.status === "open" ? "Açık" : "Kapalı"}</Badge> },
        ]} />
      )}
      {tab === "menu" && (
        <SimpleTable rows={menu} columns={[
          { key: "name", header: t('fnb.itemName') },
          { key: "category", header: t('fnb.category') },
          { key: "price", header: t('fnb.price'), align: "right", render: (m) => tl(m.price) },
          { key: "margin", header: "Marj", align: "right", render: (m) => (m.price > 0 ? `%${Math.round(((m.price - m.cost) / m.price) * 100)}` : "—") },
          { key: "popular", header: "Popüler", render: (m) => (m.popular ? <Badge tone="success">★</Badge> : "—") },
        ]} />
      )}
    </div>
  );
}
