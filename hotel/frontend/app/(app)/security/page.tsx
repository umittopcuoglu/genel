"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_ACCESS_LOGS, MOCK_KEYCARDS, MOCK_KVKK } from "@/lib/mock-faz34";

const KVKK_TONE: Record<string, BadgeTone> = { granted: "success", pending: "warning", completed: "info" };

export default function SecurityPage() {
  const [tab, setTab] = useState<"access" | "cards" | "kvkk">("access");

  return (
    <div className="space-y-6">
      <PageHeader title="Güvenlik & Erişim & KVKK" subtitle="Kapı/kart erişimleri, anahtar kartları, KVKK uyum" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Bugünkü Erişim" value={String(MOCK_ACCESS_LOGS.length)} />
        <StatCard label="Reddedilen" value={String(MOCK_ACCESS_LOGS.filter((a) => a.result === "denied").length)} tone="danger" />
        <StatCard label="Aktif Kart" value={String(MOCK_KEYCARDS.filter((k) => k.status === "active").length)} />
        <StatCard label="Bekleyen KVKK" value={String(MOCK_KVKK.filter((k) => k.status === "pending").length)} tone="warning" />
      </div>

      <AIPanel
        agent="SecureAI"
        suggestion="Oda 305'te 03:14'te reddedilen erişim tespit edildi — kart süresi dolmuş ama 4 deneme yapılmış. Olası yetkisiz giriş; güvenliğe bildirim önerilir."
        rationale="Erişim log anomali taraması · gece saati + tekrarlı deneme"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["access", "Erişim Logları"], ["cards", "Anahtar Kartları"], ["kvkk", "KVKK Talepleri"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "access" && (
        <SimpleTable rows={MOCK_ACCESS_LOGS} columns={[
          { key: "area", header: "Bölge" },
          { key: "card", header: "Kart" },
          { key: "who", header: "Kişi" },
          { key: "time", header: "Zaman" },
          { key: "result", header: "Sonuç", render: (a) => <Badge tone={a.result === "granted" ? "success" : "danger"}>{a.result === "granted" ? "İzin" : "Red"}</Badge> },
        ]} />
      )}
      {tab === "cards" && (
        <SimpleTable rows={MOCK_KEYCARDS} columns={[
          { key: "code", header: "Kart No" },
          { key: "owner", header: "Sahip" },
          { key: "type", header: "Tip", render: (k) => <Badge tone={k.type === "guest" ? "info" : "primary"}>{k.type === "guest" ? "Misafir" : "Personel"}</Badge> },
          { key: "valid", header: "Geçerlilik" },
          { key: "status", header: "Durum", render: (k) => <Badge tone={k.status === "active" ? "success" : "neutral"}>{k.status === "active" ? "Aktif" : "Süresi dolmuş"}</Badge> },
        ]} />
      )}
      {tab === "kvkk" && (
        <SimpleTable rows={MOCK_KVKK} columns={[
          { key: "guest", header: "Misafir" },
          { key: "purpose", header: "Amaç / Talep" },
          { key: "date", header: "Tarih" },
          { key: "status", header: "Durum", render: (k) => <Badge tone={KVKK_TONE[k.status]}>{k.status === "granted" ? "Onaylı" : k.status === "pending" ? "Bekliyor" : "Tamamlandı"}</Badge> },
        ]} />
      )}
    </div>
  );
}
