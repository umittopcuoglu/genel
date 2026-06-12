"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_OUTLETS, MOCK_CHECKS, MOCK_MENU } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

export default function FnbPage() {
  const [tab, setTab] = useState<"outlets" | "checks" | "menu">("outlets");
  const todayTotal = MOCK_OUTLETS.reduce((s, o) => s + o.todaySales, 0);

  return (
    <div className="space-y-6">
      <PageHeader title="F&B / POS" subtitle={`${MOCK_OUTLETS.length} satış noktası · dış POS entegrasyonu (mock)`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Bugünkü F&B Geliri" value={tl(todayTotal)} tone="success" />
        <StatCard label="Açık Adisyon" value={String(MOCK_CHECKS.filter((c) => c.status === "open").length)} />
        <StatCard label="Satış Noktası" value={String(MOCK_OUTLETS.length)} />
        <StatCard label="Menü Kalemi" value={String(MOCK_MENU.length)} />
      </div>

      <AIPanel
        agent="ChefIQ AI"
        suggestion="Izgara Levrek talebi hafta sonu %35 artıyor; 18 kg ek stok önerilir. Tiramisu kâr marjı yüksek ama düşük popülerlik — menüde öne çıkarın."
        rationale="Geçmiş satış + kâr/popülerlik matrisi"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["outlets", "Satış Noktaları"], ["checks", "Adisyonlar"], ["menu", "Menü"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "outlets" && (
        <SimpleTable rows={MOCK_OUTLETS} columns={[
          { key: "name", header: "Nokta" },
          { key: "type", header: "Tip" },
          { key: "open", header: "Durum", render: (o) => (o.open ? <Badge tone="success">Açık</Badge> : <Badge>Kapalı</Badge>) },
          { key: "todaySales", header: "Bugünkü Satış", align: "right", render: (o) => tl(o.todaySales) },
        ]} />
      )}
      {tab === "checks" && (
        <SimpleTable rows={MOCK_CHECKS} columns={[
          { key: "outlet", header: "Nokta" },
          { key: "table", header: "Masa" },
          { key: "room", header: "Oda", render: (c) => c.room ?? "—" },
          { key: "items", header: "Kalem", align: "right" },
          { key: "total", header: "Tutar", align: "right", render: (c) => tl(c.total) },
          { key: "status", header: "Durum", render: (c) => <Badge tone={c.status === "open" ? "info" : "neutral"}>{c.status === "open" ? "Açık" : "Kapalı"}</Badge> },
        ]} />
      )}
      {tab === "menu" && (
        <SimpleTable rows={MOCK_MENU} columns={[
          { key: "name", header: "Ürün" },
          { key: "category", header: "Kategori" },
          { key: "price", header: "Fiyat", align: "right", render: (m) => tl(m.price) },
          { key: "margin", header: "Marj", align: "right", render: (m) => `%${Math.round(((m.price - m.cost) / m.price) * 100)}` },
          { key: "popular", header: "Popüler", render: (m) => (m.popular ? <Badge tone="success">★</Badge> : "—") },
        ]} />
      )}
    </div>
  );
}
