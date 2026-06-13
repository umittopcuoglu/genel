"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
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
  const { t } = useTranslation();
  const [tab, setTab] = useState<"groups" | "events">("groups");
  const totalPax = MOCK_GROUPS.reduce((s, g) => s + g.pax, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('groups.title')}
        subtitle={`${MOCK_GROUPS.length} grup · ${MOCK_EVENTS.length} etkinlik`}
        action={
          <button onClick={() => toast.info("Coming soon")} className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90">
            <Plus className="h-4 w-4" /> {t('groups.newGroup')}
          </button>
        }
      />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Aktif Grup" value={String(MOCK_GROUPS.filter((g) => g.status === "confirmed").length)} tone="success" />
        <StatCard label={t('groups.pax')} value={String(totalPax)} />
        <StatCard label="Bloklu Oda" value={String(MOCK_GROUPS.reduce((s, g) => s + g.blocks, 0))} />
        <StatCard label={t('groups.events')} value={String(MOCK_EVENTS.length)} />
      </div>

      <AIPanel
        agent="EventIQ AI"
        suggestion="Touresco Conference ballroom at 90% capacity. Moving networking cocktail to terrace could increase F&B revenue by ₺14,000."
        rationale="Event type + venue availability + historical upsell rates"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["groups", t('groups.groupName')], ["events", t('groups.events')]].map(([id, label]) => (
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
            { key: "name", header: t('groups.groupName') },
            { key: "dates", header: t('common.date'), render: (g) => `${g.start} → ${g.end}` },
            { key: "pax", header: t('groups.pax'), align: "right" },
            { key: "blocks", header: "Blok", align: "right" },
            { key: "discount", header: "İndirim", align: "right", render: (g) => `%${g.discount}` },
            { key: "status", header: t('common.status'), render: (g) => <Badge tone={STATUS[g.status].tone}>{STATUS[g.status].label}</Badge> },
          ]}
        />
      ) : (
        <SimpleTable
          rows={MOCK_EVENTS}
          columns={[
            { key: "title", header: t('groups.venue') },
            { key: "group", header: t('groups.groupName') },
            { key: "venue", header: t('groups.venue') },
            { key: "capacity", header: t('groups.capacity'), align: "right" },
            { key: "setup", header: t('groups.setupType') },
            { key: "date", header: t('common.date') },
            { key: "catering", header: "Catering", render: (e) => (e.catering ? <Badge tone="success">Var</Badge> : <Badge>Yok</Badge>) },
          ]}
        />
      )}
    </div>
  );
}
