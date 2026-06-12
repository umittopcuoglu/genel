"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_BLOCKCHAIN_IDS, MOCK_CREDENTIALS } from "@/lib/mock-faz34";

export default function BlockchainPage() {
  const [tab, setTab] = useState<"identities" | "credentials">("identities");

  return (
    <div className="space-y-6">
      <PageHeader title="Blockchain Misafir Kimliği (SSI)" subtitle="W3C VC · DID · zero-knowledge proof (Polygon mock)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="DID Kimlik" value={String(MOCK_BLOCKCHAIN_IDS.length)} />
        <StatCard label="Doğrulanmış" value={String(MOCK_BLOCKCHAIN_IDS.filter((b) => b.verified).length)} tone="success" />
        <StatCard label="Credential (VC)" value={String(MOCK_CREDENTIALS.length)} />
        <StatCard label="İptal Edilen" value={String(MOCK_CREDENTIALS.filter((c) => c.status === "revoked").length)} tone="danger" />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["identities", "Kimlikler (DID)"], ["credentials", "Credentials (VC)"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "identities" ? (
        <SimpleTable rows={MOCK_BLOCKCHAIN_IDS} columns={[
          { key: "guest", header: "Misafir" },
          { key: "did", header: "DID", render: (b) => <span className="font-mono text-xs">{b.did}</span> },
          { key: "credentials", header: "VC", align: "right" },
          { key: "verified", header: "Doğrulama", render: (b) => <Badge tone={b.verified ? "success" : "warning"}>{b.verified ? "Doğrulandı" : "Bekliyor"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_CREDENTIALS} columns={[
          { key: "subject", header: "Sahip" },
          { key: "type", header: "Tür" },
          { key: "issuer", header: "İhraç Eden", render: (c) => <span className="font-mono text-xs">{c.issuer}</span> },
          { key: "status", header: "Durum", render: (c) => <Badge tone={c.status === "active" ? "success" : "danger"}>{c.status === "active" ? "Aktif" : "İptal"}</Badge> },
        ]} />
      )}
    </div>
  );
}
