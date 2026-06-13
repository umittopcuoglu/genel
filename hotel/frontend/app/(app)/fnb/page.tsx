"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_OUTLETS, MOCK_CHECKS, MOCK_MENU } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

export default function FnbPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"outlets" | "checks" | "menu">("outlets");
  const todayTotal = MOCK_OUTLETS.reduce((s, o) => s + o.todaySales, 0);

  const tabs = [
    { id: "outlets", label: t('fnb.outlets') },
    { id: "checks", label: "Adisyonlar" },
    { id: "menu", label: "Menü" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t('fnb.title')} subtitle={`${MOCK_OUTLETS.length} satış noktası · dış POS entegrasyonu (mock)`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Bugünkü F&B Geliri" value={tl(todayTotal)} tone="success" />
        <StatCard label="Açık Adisyon" value={String(MOCK_CHECKS.filter((c) => c.status === "open").length)} />
        <StatCard label={t('fnb.outlets')} value={String(MOCK_OUTLETS.length)} />
        <StatCard label="Menü Kalemi" value={String(MOCK_MENU.length)} />
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
        <SimpleTable rows={MOCK_OUTLETS} columns={[
          { key: "name", header: t('fnb.outletName') },
          { key: "type", header: t('fnb.category') },
          { key: "open", header: t('common.status'), render: (o) => (o.open ? <Badge tone="success">Açık</Badge> : <Badge>Kapalı</Badge>) },
          { key: "todaySales", header: "Bugünkü Satış", align: "right", render: (o) => tl(o.todaySales) },
        ]} />
      )}
      {tab === "checks" && (
        <SimpleTable rows={MOCK_CHECKS} columns={[
          { key: "outlet", header: t('fnb.outlets') },
          { key: "table", header: "Masa" },
          { key: "room", header: "Oda", render: (c) => c.room ?? "—" },
          { key: "items", header: t('fnb.quantity'), align: "right" },
          { key: "total", header: t('fnb.total'), align: "right", render: (c) => tl(c.total) },
          { key: "status", header: t('common.status'), render: (c) => <Badge tone={c.status === "open" ? "info" : "neutral"}>{c.status === "open" ? "Açık" : "Kapalı"}</Badge> },
        ]} />
      )}
      {tab === "menu" && (
        <SimpleTable rows={MOCK_MENU} columns={[
          { key: "name", header: t('fnb.itemName') },
          { key: "category", header: t('fnb.category') },
          { key: "price", header: t('fnb.price'), align: "right", render: (m) => tl(m.price) },
          { key: "margin", header: "Marj", align: "right", render: (m) => `%${Math.round(((m.price - m.cost) / m.price) * 100)}` },
          { key: "popular", header: "Popüler", render: (m) => (m.popular ? <Badge tone="success">★</Badge> : "—") },
        ]} />
      )}
    </div>
  );
}
