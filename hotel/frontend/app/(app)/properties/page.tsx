"use client";

import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Card } from "@/components/ui/Card";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_CHAIN, MOCK_PROPERTIES } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${(n / 1_000_000).toFixed(1)}M`;

// Backend (console.PropertyResponse) → ekran satır şekli normalizasyonu.
type PropertyRow = { id: string; name: string; city: string; rooms: number; occupancy: number; revenue: number };

function normalizeProperties(raw: any[]): PropertyRow[] {
  return raw.map((p) => ({
    id: String(p.id),
    name: p.name,
    city: p.city ?? "—",
    rooms: Number(p.total_rooms ?? 0),
    occupancy: 0, // doluluk PropertyResponse'ta yok
    revenue: 0, // gelir PropertyResponse'ta yok
  }));
}

export default function PropertiesPage() {
  const { t } = useTranslation();

  const { data: propsRaw, usingFallback: propsFallback } = useApiData<any[]>({
    path: "/api/v1/console/properties",
    fallback: MOCK_PROPERTIES,
  });

  const properties = propsFallback ? MOCK_PROPERTIES : normalizeProperties(propsRaw);
  const usingFallback = propsFallback;

  const totalRooms = properties.reduce((s, p) => s + p.rooms, 0);
  const totalRev = properties.reduce((s, p) => s + p.revenue, 0);
  const avgOcc = properties.length ? Math.round(properties.reduce((s, p) => s + p.occupancy, 0) / properties.length) : 0;

  return (
    <div className="space-y-6">
      <PageHeader title={`${t('properties.title')} — ${MOCK_CHAIN.name}`} subtitle={`${MOCK_CHAIN.properties} properties · consolidated reporting`} />

      {usingFallback && <MockBanner />}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('properties.properties')} value={String(properties.length)} />
        <StatCard label={t('properties.rooms')} value={String(totalRooms)} />
        <StatCard label={t('properties.occupancy')} value={`%${avgOcc}`} tone="success" />
        <StatCard label="Chain Revenue" value={tl(totalRev)} tone="success" />
      </div>

      <AIPanel
        agent="ChainIQ AI"
        suggestion="Antalya Resort at 92% occupancy leads; Istanbul Bosphorus at 86% but high ADR potential. Corporate campaign on weekdays in Istanbul forecasts +4% occupancy."
        rationale="Consolidated occupancy/revenue comparison · city-based demand"
      />

      <Card title={t('properties.properties')}>
        <SimpleTable rows={properties} columns={[
          { key: "name", header: t('properties.propertyName') },
          { key: "city", header: t('properties.location') },
          { key: "rooms", header: t('properties.rooms'), align: "right" },
          { key: "occupancy", header: t('properties.occupancy'), align: "right", render: (p) => <span className={p.occupancy >= 90 ? "text-success" : ""}>%{p.occupancy}</span> },
          { key: "revenue", header: t('properties.revenue'), align: "right", render: (p) => tl(p.revenue) },
        ]} />
      </Card>
    </div>
  );
}
