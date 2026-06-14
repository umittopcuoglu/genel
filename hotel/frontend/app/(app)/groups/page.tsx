"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_GROUPS, MOCK_EVENTS } from "@/lib/mock-faz34";
import { toast } from "@/components/ui/Toast";

const STATUS: Record<string, { tone: BadgeTone; label: string }> = {
  inquiry: { tone: "warning", label: "Sorgu" },
  confirmed: { tone: "success", label: "Onaylı" },
  completed: { tone: "neutral", label: "Tamamlandı" },
  cancelled: { tone: "danger", label: "İptal" },
};

// Backend (GroupResponse) → ekran satır şekli normalizasyonu.
function normalizeGroups(raw: any[]) {
  return raw.map((g) => ({
    id: String(g.id),
    name: g.name,
    start: g.block_start_date,
    end: g.block_end_date,
    pax: g.pax_count,
    blocks: 0, // backend has no block count → 0
    discount: Number(g.discount_rate ?? 0),
    status: g.status,
  }));
}

export default function GroupsPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"groups" | "events">("groups");

  const { data: groupsRaw, usingFallback: groupsFallback } = useApiData<any[]>({
    path: "/api/v1/groups",
    fallback: MOCK_GROUPS,
  });

  const groups = groupsFallback ? MOCK_GROUPS : normalizeGroups(groupsRaw);
  // Etkinlikler için backend toplu uç sağlamıyor → mock kalır.
  const usingFallback = groupsFallback;

  const totalPax = groups.reduce((s, g) => s + g.pax, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('groups.title')}
        subtitle={`${groups.length} grup · ${MOCK_EVENTS.length} etkinlik`}
        action={
          <button onClick={() => toast.info("Coming soon")} className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90">
            <Plus className="h-4 w-4" /> {t('groups.newGroup')}
          </button>
        }
      />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Aktif Grup" value={String(groups.filter((g) => g.status === "confirmed").length)} tone="success" />
        <StatCard label={t('groups.pax')} value={String(totalPax)} />
        <StatCard label="Bloklu Oda" value={String(groups.reduce((s, g) => s + g.blocks, 0))} />
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
          rows={groups}
          columns={[
            { key: "name", header: t('groups.groupName') },
            { key: "dates", header: t('common.date'), render: (g) => `${g.start} → ${g.end}` },
            { key: "pax", header: t('groups.pax'), align: "right" },
            { key: "blocks", header: "Blok", align: "right" },
            { key: "discount", header: "İndirim", align: "right", render: (g) => `%${g.discount}` },
            { key: "status", header: t('common.status'), render: (g) => { const s = STATUS[g.status] ?? { tone: "neutral" as BadgeTone, label: g.status }; return <Badge tone={s.tone}>{s.label}</Badge>; } },
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
