"use client";

import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Card } from "@/components/ui/Card";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_CHAIN, MOCK_PROPERTIES } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${(n / 1_000_000).toFixed(1)}M`;

export default function PropertiesPage() {
  const totalRooms = MOCK_PROPERTIES.reduce((s, p) => s + p.rooms, 0);
  const totalRev = MOCK_PROPERTIES.reduce((s, p) => s + p.revenue, 0);
  const avgOcc = Math.round(MOCK_PROPERTIES.reduce((s, p) => s + p.occupancy, 0) / MOCK_PROPERTIES.length);

  return (
    <div className="space-y-6">
      <PageHeader title={`Çoklu Tesis — ${MOCK_CHAIN.name}`} subtitle={`${MOCK_CHAIN.properties} tesis · konsolide raporlama`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Tesis" value={String(MOCK_PROPERTIES.length)} />
        <StatCard label="Toplam Oda" value={String(totalRooms)} />
        <StatCard label="Ort. Doluluk" value={`%${avgOcc}`} tone="success" />
        <StatCard label="Zincir Geliri" value={tl(totalRev)} tone="success" />
      </div>

      <AIPanel
        agent="ChainIQ AI"
        suggestion="Antalya Resort %92 doluluk ile zirvede; İstanbul Bosphorus %86 ama ADR potansiyeli yüksek. İstanbul'da hafta içi kurumsal kampanya ile +%4 doluluk öngörülüyor."
        rationale="Konsolide doluluk/gelir karşılaştırması · şehir bazlı talep"
      />

      <Card title="Tesisler">
        <SimpleTable rows={MOCK_PROPERTIES} columns={[
          { key: "name", header: "Tesis" },
          { key: "city", header: "Şehir" },
          { key: "rooms", header: "Oda", align: "right" },
          { key: "occupancy", header: "Doluluk", align: "right", render: (p) => <span className={p.occupancy >= 90 ? "text-success" : ""}>%{p.occupancy}</span> },
          { key: "revenue", header: "Aylık Gelir", align: "right", render: (p) => tl(p.revenue) },
        ]} />
      </Card>
    </div>
  );
}
