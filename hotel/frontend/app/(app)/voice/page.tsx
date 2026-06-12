"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_VOICE_INTEGRATIONS, MOCK_VOICE_COMMANDS } from "@/lib/mock-faz34";

export default function VoicePage() {
  const [tab, setTab] = useState<"integrations" | "commands">("integrations");

  return (
    <div className="space-y-6">
      <PageHeader title="Sesli Kontrol" subtitle="Alexa for Hospitality · Google Nest (webhook mock)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Entegrasyon" value={String(MOCK_VOICE_INTEGRATIONS.length)} />
        <StatCard label="Donanımlı Oda" value={String(MOCK_VOICE_INTEGRATIONS.reduce((s, v) => s + v.rooms, 0))} tone="success" />
        <StatCard label="Bugünkü Komut" value={String(MOCK_VOICE_COMMANDS.length)} />
        <StatCard label="Başarılı" value={String(MOCK_VOICE_COMMANDS.filter((c) => c.result === "success").length)} tone="success" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["integrations", "Entegrasyonlar"], ["commands", "Komut Geçmişi"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "integrations" ? (
        <SimpleTable rows={MOCK_VOICE_INTEGRATIONS} columns={[
          { key: "name", header: "Entegrasyon" },
          { key: "provider", header: "Sağlayıcı", render: (v) => <Badge tone="primary">{v.provider}</Badge> },
          { key: "rooms", header: "Oda", align: "right" },
          { key: "active", header: "Durum", render: (v) => <Badge tone={v.active ? "success" : "neutral"}>{v.active ? "Aktif" : "Pasif"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_VOICE_COMMANDS} columns={[
          { key: "room", header: "Oda" },
          { key: "intent", header: "Intent" },
          { key: "phrase", header: "İfade" },
          { key: "time", header: "Zaman" },
          { key: "result", header: "Sonuç", render: (c) => <Badge tone={c.result === "success" ? "success" : "info"}>{c.result === "success" ? "Başarılı" : "Yönlendirildi"}</Badge> },
        ]} />
      )}
    </div>
  );
}
