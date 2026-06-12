"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_GDS_CHANNELS, MOCK_GDS_RES, MOCK_GDS_LOGS } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;
const LOG_TONE: Record<string, BadgeTone> = { success: "success", partial: "warning", failed: "danger" };

export default function GdsPage() {
  const [tab, setTab] = useState<"channels" | "reservations" | "logs">("channels");

  return (
    <div className="space-y-6">
      <PageHeader title="GDS Entegrasyonu" subtitle="Amadeus / Sabre / Travelport (mock-first adapter)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Aktif Kanal" value={String(MOCK_GDS_CHANNELS.filter((c) => c.active).length)} tone="success" />
        <StatCard label="GDS Rezervasyon" value={String(MOCK_GDS_RES.length)} />
        <StatCard label="Senkron (bugün)" value={String(MOCK_GDS_LOGS.length)} />
        <StatCard label="Bekleyen" value={String(MOCK_GDS_RES.filter((r) => r.status === "pending").length)} tone="warning" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["channels", "Kanallar"], ["reservations", "Rezervasyonlar"], ["logs", "Senkron Logları"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "channels" && (
        <SimpleTable rows={MOCK_GDS_CHANNELS} columns={[
          { key: "code", header: "Kod" },
          { key: "name", header: "Sağlayıcı" },
          { key: "actions", header: "Desteklenen" },
          { key: "active", header: "Durum", render: (c) => <Badge tone={c.active ? "success" : "neutral"}>{c.active ? "Aktif" : "Pasif"}</Badge> },
        ]} />
      )}
      {tab === "reservations" && (
        <SimpleTable rows={MOCK_GDS_RES} columns={[
          { key: "gdsId", header: "GDS No" },
          { key: "guest", header: "Misafir" },
          { key: "channel", header: "Kanal" },
          { key: "checkin", header: "Giriş" },
          { key: "nights", header: "Gece", align: "right" },
          { key: "total", header: "Tutar", align: "right", render: (r) => tl(r.total) },
          { key: "status", header: "Durum", render: (r) => <Badge tone={r.status === "synced" ? "success" : "warning"}>{r.status === "synced" ? "Senkronize" : "Bekliyor"}</Badge> },
        ]} />
      )}
      {tab === "logs" && (
        <SimpleTable rows={MOCK_GDS_LOGS} columns={[
          { key: "channel", header: "Kanal" },
          { key: "action", header: "İşlem" },
          { key: "time", header: "Zaman" },
          { key: "ms", header: "Süre", align: "right", render: (l) => `${l.ms} ms` },
          { key: "status", header: "Sonuç", render: (l) => <Badge tone={LOG_TONE[l.status]}>{l.status}</Badge> },
        ]} />
      )}
    </div>
  );
}
