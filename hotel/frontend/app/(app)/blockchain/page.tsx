"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_BLOCKCHAIN_IDS, MOCK_CREDENTIALS } from "@/lib/mock-faz34";

export default function BlockchainPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"identities" | "credentials">("identities");

  return (
    <div className="space-y-6">
      <PageHeader title={t('blockchain.title')} subtitle={t('blockchain.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('blockchain.credentials')} value={String(MOCK_BLOCKCHAIN_IDS.length)} />
        <StatCard label={t('blockchain.verified')} value={String(MOCK_BLOCKCHAIN_IDS.filter((b) => b.verified).length)} tone="success" />
        <StatCard label="Credentials (VC)" value={String(MOCK_CREDENTIALS.length)} />
        <StatCard label="Revoked" value={String(MOCK_CREDENTIALS.filter((c) => c.status === "revoked").length)} tone="danger" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["identities", t('blockchain.guestId')], ["credentials", "Credentials (VC)"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "identities" ? (
        <SimpleTable rows={MOCK_BLOCKCHAIN_IDS} columns={[
          { key: "guest", header: "Guest" },
          { key: "did", header: "DID", render: (b) => <span className="font-mono text-xs">{b.did}</span> },
          { key: "credentials", header: "Credentials", align: "right" },
          { key: "verified", header: t('blockchain.verification'), render: (b) => <Badge tone={b.verified ? "success" : "warning"}>{b.verified ? t('blockchain.verified') : t('blockchain.pending')}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_CREDENTIALS} columns={[
          { key: "subject", header: "Subject" },
          { key: "type", header: "Type" },
          { key: "issuer", header: "Issuer", render: (c) => <span className="font-mono text-xs">{c.issuer}</span> },
          { key: "status", header: t('common.status'), render: (c) => <Badge tone={c.status === "active" ? "success" : "danger"}>{c.status === "active" ? "Active" : "Revoked"}</Badge> },
        ]} />
      )}
    </div>
  );
}
