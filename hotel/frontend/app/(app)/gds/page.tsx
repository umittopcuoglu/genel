"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_GDS_CHANNELS, MOCK_GDS_RES, MOCK_GDS_LOGS } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;
const LOG_TONE: Record<string, BadgeTone> = { success: "success", partial: "warning", failed: "danger" };

export default function GdsPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"channels" | "reservations" | "logs">("channels");

  return (
    <div className="space-y-6">
      <PageHeader title={t('gds.title')} subtitle={t('gds.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('gds.activeConnections')} value={String(MOCK_GDS_CHANNELS.filter((c) => c.active).length)} tone="success" />
        <StatCard label="GDS Reservations" value={String(MOCK_GDS_RES.length)} />
        <StatCard label="Sync (today)" value={String(MOCK_GDS_LOGS.length)} />
        <StatCard label="Pending" value={String(MOCK_GDS_RES.filter((r) => r.status === "pending").length)} tone="warning" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["channels", t('gds.connections')], ["reservations", "Reservations"], ["logs", "Sync Logs"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "channels" && (
        <SimpleTable rows={MOCK_GDS_CHANNELS} columns={[
          { key: "code", header: "Code" },
          { key: "name", header: t('gds.provider') },
          { key: "actions", header: "Supported" },
          { key: "active", header: t('common.status'), render: (c) => <Badge tone={c.active ? "success" : "neutral"}>{c.active ? "Active" : "Inactive"}</Badge> },
        ]} />
      )}
      {tab === "reservations" && (
        <SimpleTable rows={MOCK_GDS_RES} columns={[
          { key: "gdsId", header: "GDS ID" },
          { key: "guest", header: "Guest" },
          { key: "channel", header: "Channel" },
          { key: "checkin", header: "Check-in" },
          { key: "nights", header: "Nights", align: "right" },
          { key: "total", header: "Amount", align: "right", render: (r) => tl(r.total) },
          { key: "status", header: t('common.status'), render: (r) => <Badge tone={r.status === "synced" ? "success" : "warning"}>{r.status === "synced" ? "Synced" : "Pending"}</Badge> },
        ]} />
      )}
      {tab === "logs" && (
        <SimpleTable rows={MOCK_GDS_LOGS} columns={[
          { key: "channel", header: "Channel" },
          { key: "action", header: "Action" },
          { key: "time", header: "Time" },
          { key: "ms", header: "Duration", align: "right", render: (l) => `${l.ms} ms` },
          { key: "status", header: "Result", render: (l) => <Badge tone={LOG_TONE[l.status]}>{l.status}</Badge> },
        ]} />
      )}
    </div>
  );
}
