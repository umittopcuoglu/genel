"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_VOICE_INTEGRATIONS, MOCK_VOICE_COMMANDS } from "@/lib/mock-faz34";

export default function VoicePage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"integrations" | "commands">("integrations");

  return (
    <div className="space-y-6">
      <PageHeader title={t('voice.title')} subtitle={t('voice.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Integrations" value={String(MOCK_VOICE_INTEGRATIONS.length)} />
        <StatCard label="Equipped Rooms" value={String(MOCK_VOICE_INTEGRATIONS.reduce((s, v) => s + v.rooms, 0))} tone="success" />
        <StatCard label="Today's Commands" value={String(MOCK_VOICE_COMMANDS.length)} />
        <StatCard label="Successful" value={String(MOCK_VOICE_COMMANDS.filter((c) => c.result === "success").length)} tone="success" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["integrations", "Integrations"], ["commands", "Command History"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "integrations" ? (
        <SimpleTable rows={MOCK_VOICE_INTEGRATIONS} columns={[
          { key: "name", header: "Name" },
          { key: "provider", header: t('gds.provider'), render: (v) => <Badge tone="primary">{v.provider}</Badge> },
          { key: "rooms", header: t('properties.rooms'), align: "right" },
          { key: "active", header: t('common.status'), render: (v) => <Badge tone={v.active ? "success" : "neutral"}>{v.active ? "Active" : "Inactive"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_VOICE_COMMANDS} columns={[
          { key: "room", header: t('cv.room') },
          { key: "intent", header: "Intent" },
          { key: "phrase", header: "Phrase" },
          { key: "time", header: "Time" },
          { key: "result", header: "Result", render: (c) => <Badge tone={c.result === "success" ? "success" : "info"}>{c.result === "success" ? "Success" : "Routed"}</Badge> },
        ]} />
      )}
    </div>
  );
}
