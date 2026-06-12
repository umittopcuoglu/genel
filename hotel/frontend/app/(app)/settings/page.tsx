"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { MOCK_USERS, ROLES } from "@/lib/mock-modules";

/**
 * Ayarlar — kullanıcılar + roller (RBAC) + genel yapılandırma (docs/03 §6).
 * Backend: /api/v1/auth/users + roller (TASK-001) bağlanınca canlanır.
 */
export default function SettingsPage() {
  const [tab, setTab] = useState<"users" | "roles" | "general">("users");

  return (
    <div className="space-y-6">
      <PageHeader title="Ayarlar" subtitle="Kullanıcılar, roller ve sistem yapılandırması" mock={false} />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[
            { id: "users", label: "Kullanıcılar" },
            { id: "roles", label: "Roller (RBAC)" },
            { id: "general", label: "Genel" },
          ].map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id as typeof tab)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === t.id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {tab === "users" && (
        <Card
          title="Kullanıcılar"
          action={
            <button
              onClick={() => alert("Yeni kullanıcı — backend TASK-001 bekleniyor")}
              className="flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-white hover:opacity-90"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden /> Yeni Kullanıcı
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                  <th className="px-2 py-2 font-medium">Ad</th>
                  <th className="px-2 py-2 font-medium">E-posta</th>
                  <th className="px-2 py-2 font-medium">Rol</th>
                  <th className="px-2 py-2 font-medium">Durum</th>
                  <th className="px-2 py-2 font-medium">Son Giriş</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_USERS.map((u) => (
                  <tr key={u.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                    <td className="px-2 py-2.5 font-medium">{u.name}</td>
                    <td className="px-2 py-2.5 text-text-2">{u.email}</td>
                    <td className="px-2 py-2.5"><Badge tone="primary">{u.role}</Badge></td>
                    <td className="px-2 py-2.5"><Badge tone={u.active ? "success" : "neutral"}>{u.active ? "Aktif" : "Pasif"}</Badge></td>
                    <td className="px-2 py-2.5 font-mono text-text-2">{u.last_login}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === "roles" && (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {ROLES.map((r) => (
            <Card key={r.key} title={r.label}>
              <p className="text-sm text-text-2">{r.desc}</p>
              <div className="mt-2"><Badge tone="neutral">{r.key}</Badge></div>
            </Card>
          ))}
        </div>
      )}

      {tab === "general" && (
        <Card title="Genel Yapılandırma">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {[
              { k: "Tesis Adı", v: "HotelOps Demo Resort" },
              { k: "Para Birimi", v: "TRY (₺)" },
              { k: "Saat Dilimi", v: "Europe/Istanbul (UTC+3)" },
              { k: "Check-in Saati", v: "14:00" },
              { k: "Check-out Saati", v: "12:00" },
              { k: "KDV Oranı", v: "%10 (konaklama)" },
              { k: "Dil", v: "Türkçe" },
              { k: "API Sürümü", v: "v1.0.0" },
            ].map((row) => (
              <div key={row.k} className="flex items-center justify-between border-b border-line py-2 last:border-0">
                <dt className="text-sm text-text-2">{row.k}</dt>
                <dd className="text-sm font-medium">{row.v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      )}
    </div>
  );
}
