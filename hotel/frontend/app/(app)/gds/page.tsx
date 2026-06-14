"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_GDS_CHANNELS, MOCK_GDS_RES, MOCK_GDS_LOGS } from "@/lib/mock-faz34";

const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;
const LOG_TONE: Record<string, BadgeTone> = { success: "success", partial: "warning", failed: "danger" };

// Backend (GDS) → ekran satır şekli normalizasyonu.
function normalizeChannels(raw: any[]) {
  return raw.map((c) => ({
    id: String(c.id),
    code: c.code,
    name: c.name,
    provider: c.provider,
    active: c.is_active,
    actions: "—",
  }));
}

function normalizeReservations(raw: any[]) {
  return raw.map((r) => ({
    id: String(r.id),
    gdsId: r.gds_reservation_id,
    guest: r.guest_name,
    channel: "—",
    checkin: (r.check_in ?? "").slice(0, 10),
    nights: 0,
    status: r.status,
    total: Number(r.total_amount ?? 0),
  }));
}

function normalizeLogs(raw: any[]) {
  return raw.map((l) => ({
    id: String(l.id),
    channel: "—",
    action: l.action,
    status: l.status,
    time: (l.created_at ?? "").slice(0, 16).replace("T", " "),
    ms: l.duration_ms,
  }));
}

export default function GdsPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"channels" | "reservations" | "logs">("channels");

  const { data: channelsRaw, usingFallback: channelsFallback } = useApiData<any[]>({
    path: "/api/v1/gds/channels",
    fallback: MOCK_GDS_CHANNELS,
  });
  const { data: resRaw, usingFallback: resFallback } = useApiData<any[]>({
    path: "/api/v1/gds/reservations",
    fallback: MOCK_GDS_RES,
  });
  const { data: logsRaw, usingFallback: logsFallback } = useApiData<any[]>({
    path: "/api/v1/gds/sync-logs",
    fallback: MOCK_GDS_LOGS,
  });

  const channels = channelsFallback ? MOCK_GDS_CHANNELS : normalizeChannels(channelsRaw);
  const reservations = resFallback ? MOCK_GDS_RES : normalizeReservations(resRaw);
  const logs = logsFallback ? MOCK_GDS_LOGS : normalizeLogs(logsRaw);
  const usingFallback = channelsFallback || resFallback || logsFallback;

  return (
    <div className="space-y-6">
      <PageHeader title={t('gds.title')} subtitle={t('gds.subtitle')} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('gds.activeConnections')} value={String(channels.filter((c) => c.active).length)} tone="success" />
        <StatCard label="GDS Reservations" value={String(reservations.length)} />
        <StatCard label="Sync (today)" value={String(logs.length)} />
        <StatCard label="Pending" value={String(reservations.filter((r) => r.status === "pending").length)} tone="warning" />
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
        <SimpleTable rows={channels} columns={[
          { key: "code", header: "Code" },
          { key: "name", header: t('gds.provider') },
          { key: "actions", header: "Supported" },
          { key: "active", header: t('common.status'), render: (c) => <Badge tone={c.active ? "success" : "neutral"}>{c.active ? "Active" : "Inactive"}</Badge> },
        ]} />
      )}
      {tab === "reservations" && (
        <SimpleTable rows={reservations} columns={[
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
        <SimpleTable rows={logs} columns={[
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
