"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_GROUPS, MOCK_EVENTS } from "@/lib/mock-faz34";
import { toast } from "@/components/ui/Toast";

const STATUS: Record<string, { tone: BadgeTone; label: string }> = {
  inquiry: { tone: "warning", label: "Sorgu" },
  confirmed: { tone: "success", label: "Onaylı" },
  completed: { tone: "neutral", label: "Tamamlandı" },
  cancelled: { tone: "danger", label: "İptal" },
};

export default function GroupsPage() {
  const [tab, setTab] = useState<"groups" | "events">("groups");
  const totalPax = MOCK_GROUPS.reduce((s, g) => s + g.pax, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Gruplar & Etkinlik (MICE)"
        subtitle={`${MOCK_GROUPS.length} grup · ${MOCK_EVENTS.length} etkinlik`}
        action={
          <button onClick={() => toast.info("Yeni grup formu yakında eklenecek")} className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90">
            <Plus className="h-4 w-4" /> Yeni Grup
          </button>
        }
      />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Aktif Grup" value={String(MOCK_GROUPS.filter((g) => g.status === "confirmed").length)} tone="success" />
        <StatCard label="Toplam Pax" value={String(totalPax)} />
        <StatCard label="Bloklu Oda" value={String(MOCK_GROUPS.reduce((s, g) => s + g.blocks, 0))} />
        <StatCard label="Etkinlik" value={String(MOCK_EVENTS.length)} />
      </div>

      <AIPanel
        agent="EventIQ AI"
        suggestion="Touresco Konferansı için Balo Salonu kapasitesi %90 dolu. Networking kokteylini Teras'a almak F&B gelirini ₺14.000 artırabilir."
        rationale="Etkinlik tipi + salon müsaitliği + geçmiş upsell oranları"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["groups", "Gruplar"], ["events", "Etkinlikler"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "groups" ? (
        <SimpleTable
          rows={MOCK_GROUPS}
          columns={[
            { key: "name", header: "Grup" },
            { key: "dates", header: "Tarih", render: (g) => `${g.start} → ${g.end}` },
            { key: "pax", header: "Pax", align: "right" },
            { key: "blocks", header: "Blok", align: "right" },
            { key: "discount", header: "İndirim", align: "right", render: (g) => `%${g.discount}` },
            { key: "status", header: "Durum", render: (g) => <Badge tone={STATUS[g.status].tone}>{STATUS[g.status].label}</Badge> },
          ]}
        />
      ) : (
        <SimpleTable
          rows={MOCK_EVENTS}
          columns={[
            { key: "title", header: "Etkinlik" },
            { key: "group", header: "Grup" },
            { key: "venue", header: "Salon" },
            { key: "capacity", header: "Kapasite", align: "right" },
            { key: "setup", header: "Kurulum" },
            { key: "date", header: "Tarih" },
            { key: "catering", header: "Catering", render: (e) => (e.catering ? <Badge tone="success">Var</Badge> : <Badge>Yok</Badge>) },
          ]}
        />
      )}
    </div>
  );
}
