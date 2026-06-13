"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_ACCESS_LOGS, MOCK_KEYCARDS, MOCK_KVKK } from "@/lib/mock-faz34";

const KVKK_TONE: Record<string, BadgeTone> = { granted: "success", pending: "warning", completed: "info" };

export default function SecurityPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"access" | "cards" | "kvkk">("access");

  return (
    <div className="space-y-6">
      <PageHeader title={t('security.title')} subtitle={t('security.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Today's Access" value={String(MOCK_ACCESS_LOGS.length)} />
        <StatCard label="Denied" value={String(MOCK_ACCESS_LOGS.filter((a) => a.result === "denied").length)} tone="danger" />
        <StatCard label={t('security.cardStatus')} value={String(MOCK_KEYCARDS.filter((k) => k.status === "active").length)} />
        <StatCard label="Pending GDPR" value={String(MOCK_KVKK.filter((k) => k.status === "pending").length)} tone="warning" />
      </div>

      <AIPanel
        agent="SecureAI"
        suggestion="Denied access detected at Room 305 at 03:14 — card expired but 4 attempts made. Possible unauthorized entry; security notification recommended."
        rationale="Access log anomaly scan · late hour + repeated attempts"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["access", t('security.accessLogs')], ["cards", t('security.keyCards')], ["kvkk", t('security.gdprRequest')]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "access" && (
        <SimpleTable rows={MOCK_ACCESS_LOGS} columns={[
          { key: "area", header: "Area" },
          { key: "card", header: "Card" },
          { key: "who", header: "Person" },
          { key: "time", header: "Time" },
          { key: "result", header: "Result", render: (a) => <Badge tone={a.result === "granted" ? "success" : "danger"}>{a.result === "granted" ? "Granted" : "Denied"}</Badge> },
        ]} />
      )}
      {tab === "cards" && (
        <SimpleTable rows={MOCK_KEYCARDS} columns={[
          { key: "code", header: "Card ID" },
          { key: "owner", header: "Owner" },
          { key: "type", header: "Type", render: (k) => <Badge tone={k.type === "guest" ? "info" : "primary"}>{k.type === "guest" ? "Guest" : "Staff"}</Badge> },
          { key: "valid", header: "Valid" },
          { key: "status", header: t('common.status'), render: (k) => <Badge tone={k.status === "active" ? "success" : "neutral"}>{k.status === "active" ? t('security.active') : t('security.expired')}</Badge> },
        ]} />
      )}
      {tab === "kvkk" && (
        <SimpleTable rows={MOCK_KVKK} columns={[
          { key: "guest", header: "Guest" },
          { key: "purpose", header: "Purpose" },
          { key: "date", header: t('common.date') },
          { key: "status", header: t('common.status'), render: (k) => <Badge tone={KVKK_TONE[k.status]}>{k.status === "granted" ? "Granted" : k.status === "pending" ? "Pending" : "Completed"}</Badge> },
        ]} />
      )}
    </div>
  );
}
