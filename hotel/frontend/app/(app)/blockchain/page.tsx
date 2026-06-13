"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_BLOCKCHAIN_IDS, MOCK_CREDENTIALS } from "@/lib/mock-faz34";

// Backend (blockchain_identity schemas) → ekran satır şekli normalizasyonu.
type IdentityRow = { id: string; guest: string; did: string; verified: boolean; credentials: number };
type CredentialRow = { id: string; subject: string; type: string; issuer: string; status: string };

// BlockchainIdentityResponse: did, is_verified mevcut; guest adı ve VC sayısı yok → guest_id / 0.
function normalizeIdentities(raw: any[]): IdentityRow[] {
  return raw.map((b) => ({
    id: String(b.id),
    guest: String(b.guest_id ?? "—"),
    did: b.did ?? "—",
    verified: b.is_verified ?? false,
    credentials: 0, // VC sayısı identity yanıtında yok
  }));
}

// VerifiableCredentialResponse: subject_did, credential_type, issuer_did, status/is_revoked mevcut.
function normalizeCredentials(raw: any[]): CredentialRow[] {
  return raw.map((c) => ({
    id: String(c.id),
    subject: c.subject_did ?? "—",
    type: c.credential_type ?? "—",
    issuer: c.issuer_did ?? "—",
    status: c.is_revoked ? "revoked" : (c.status ?? "active"),
  }));
}

export default function BlockchainPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"identities" | "credentials">("identities");

  const { data: identitiesRaw, usingFallback: identitiesFallback } = useApiData<any[]>({
    path: "/api/v1/blockchain/identities",
    fallback: MOCK_BLOCKCHAIN_IDS,
  });
  const { data: credentialsRaw, usingFallback: credentialsFallback } = useApiData<any[]>({
    path: "/api/v1/blockchain/credentials",
    fallback: MOCK_CREDENTIALS,
  });

  const identities = identitiesFallback ? MOCK_BLOCKCHAIN_IDS : normalizeIdentities(identitiesRaw);
  const credentials = credentialsFallback ? MOCK_CREDENTIALS : normalizeCredentials(credentialsRaw);
  const usingFallback = identitiesFallback || credentialsFallback;

  return (
    <div className="space-y-6">
      <PageHeader title={t('blockchain.title')} subtitle={t('blockchain.subtitle')} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('blockchain.credentials')} value={String(identities.length)} />
        <StatCard label={t('blockchain.verified')} value={String(identities.filter((b) => b.verified).length)} tone="success" />
        <StatCard label="Credentials (VC)" value={String(credentials.length)} />
        <StatCard label="Revoked" value={String(credentials.filter((c) => c.status === "revoked").length)} tone="danger" />
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
        <SimpleTable rows={identities} columns={[
          { key: "guest", header: "Guest" },
          { key: "did", header: "DID", render: (b) => <span className="font-mono text-xs">{b.did}</span> },
          { key: "credentials", header: "Credentials", align: "right" },
          { key: "verified", header: t('blockchain.verification'), render: (b) => <Badge tone={b.verified ? "success" : "warning"}>{b.verified ? t('blockchain.verified') : t('blockchain.pending')}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={credentials} columns={[
          { key: "subject", header: "Subject" },
          { key: "type", header: "Type" },
          { key: "issuer", header: "Issuer", render: (c) => <span className="font-mono text-xs">{c.issuer}</span> },
          { key: "status", header: t('common.status'), render: (c) => <Badge tone={c.status === "active" ? "success" : "danger"}>{c.status === "active" ? "Active" : "Revoked"}</Badge> },
        ]} />
      )}
    </div>
  );
}
