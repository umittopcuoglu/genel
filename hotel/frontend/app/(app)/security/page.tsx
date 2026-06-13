"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_ACCESS_LOGS, MOCK_KEYCARDS, MOCK_KVKK } from "@/lib/mock-faz34";

const KVKK_TONE: Record<string, BadgeTone> = { granted: "success", pending: "warning", completed: "info", withdrawn: "neutral" };
const KVKK_LABEL: Record<string, string> = { granted: "Granted", pending: "Pending", completed: "Completed", withdrawn: "Withdrawn" };

const fmtTime = (iso?: string) => (iso ? iso.replace("T", " ").slice(0, 16) : "—");
const fmtDate = (iso?: string) => (iso ? iso.slice(0, 10) : "—");

// Backend (TASK-017) → ekran satır şekli normalizasyonu.
function normalizeAccess(raw: any[]) {
  return raw.map((a) => ({
    id: String(a.id),
    area: a.area,
    card: a.card_number ?? a.card ?? "—",
    who: a.person_name ?? a.who ?? "—",
    time: a.time ?? fmtTime(a.accessed_at),
    result: a.result,
  }));
}

function normalizeCards(raw: any[]) {
  return raw.map((k) => ({
    id: String(k.id),
    code: k.card_number ?? k.code,
    owner: k.owner_name ?? k.owner,
    type: k.owner_type ?? k.type,
    valid: k.valid ?? `${fmtDate(k.valid_from)} → ${fmtDate(k.valid_until)}`,
    status: k.status,
  }));
}

function normalizeKvkk(raw: any[]) {
  return raw.map((k) => ({
    id: String(k.id),
    guest: k.guest_name ?? k.guest,
    purpose: k.purpose,
    date: k.date ?? fmtDate(k.consent_date),
    status: k.status,
  }));
}

export default function SecurityPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"access" | "cards" | "kvkk">("access");

  const { data: accessRaw, usingFallback: accessFallback } = useApiData<any[]>({
    path: "/api/v1/security/access-logs",
    fallback: MOCK_ACCESS_LOGS,
  });
  const { data: cardsRaw, usingFallback: cardsFallback } = useApiData<any[]>({
    path: "/api/v1/security/key-cards",
    fallback: MOCK_KEYCARDS,
  });
  const { data: kvkkRaw, usingFallback: kvkkFallback } = useApiData<any[]>({
    path: "/api/v1/security/kvkk/consents",
    fallback: MOCK_KVKK,
  });

  const accessLogs = accessFallback ? MOCK_ACCESS_LOGS : normalizeAccess(accessRaw);
  const keyCards = cardsFallback ? MOCK_KEYCARDS : normalizeCards(cardsRaw);
  const kvkk = kvkkFallback ? MOCK_KVKK : normalizeKvkk(kvkkRaw);
  const usingFallback = accessFallback || cardsFallback || kvkkFallback;

  return (
    <div className="space-y-6">
      <PageHeader title={t('security.title')} subtitle={t('security.subtitle')} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Today's Access" value={String(accessLogs.length)} />
        <StatCard label="Denied" value={String(accessLogs.filter((a) => a.result === "denied").length)} tone="danger" />
        <StatCard label={t('security.cardStatus')} value={String(keyCards.filter((k) => k.status === "active").length)} />
        <StatCard label="Pending GDPR" value={String(kvkk.filter((k) => k.status === "pending").length)} tone="warning" />
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
        <SimpleTable rows={accessLogs} columns={[
          { key: "area", header: "Area" },
          { key: "card", header: "Card" },
          { key: "who", header: "Person" },
          { key: "time", header: "Time" },
          { key: "result", header: "Result", render: (a) => <Badge tone={a.result === "granted" ? "success" : "danger"}>{a.result === "granted" ? "Granted" : "Denied"}</Badge> },
        ]} />
      )}
      {tab === "cards" && (
        <SimpleTable rows={keyCards} columns={[
          { key: "code", header: "Card ID" },
          { key: "owner", header: "Owner" },
          { key: "type", header: "Type", render: (k) => <Badge tone={k.type === "guest" ? "info" : "primary"}>{k.type === "guest" ? "Guest" : "Staff"}</Badge> },
          { key: "valid", header: "Valid" },
          { key: "status", header: t('common.status'), render: (k) => <Badge tone={k.status === "active" ? "success" : "neutral"}>{k.status === "active" ? t('security.active') : t('security.expired')}</Badge> },
        ]} />
      )}
      {tab === "kvkk" && (
        <SimpleTable rows={kvkk} columns={[
          { key: "guest", header: "Guest" },
          { key: "purpose", header: "Purpose" },
          { key: "date", header: t('common.date') },
          { key: "status", header: t('common.status'), render: (k) => <Badge tone={KVKK_TONE[k.status] ?? "neutral"}>{KVKK_LABEL[k.status] ?? k.status}</Badge> },
        ]} />
      )}
    </div>
  );
}
