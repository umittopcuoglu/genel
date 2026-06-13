"use client";

import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { MOCK_USERS, ROLES } from "@/lib/mock-modules";
import { UserCreateModal } from "@/components/UserCreateModal";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

/**
 * Ayarlar — kullanıcılar + roller (RBAC) + genel yapılandırma (docs/03 §6).
 * Backend: /api/v1/auth/users + roller (TASK-001) bağlanınca canlanır.
 */
interface ApiUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

export default function SettingsPage() {
  const [tab, setTab] = useState<"users" | "roles" | "general">("users");
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const response = await fetch("/api/v1/auth/users", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Kullanıcı listesi alınamadı:", err);
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    if (tab === "users") {
      fetchUsers();
    }
  }, [tab]);

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
              onClick={() => setModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-white hover:opacity-90"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden /> Yeni Kullanıcı
            </button>
          }
        >
          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="py-8 text-center text-text-2 text-sm">Yükleniyor...</div>
            ) : users.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-text-2 text-sm mb-3">Henüz kullanıcı yok (mock veri gösteriliyor)</p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                      <th className="px-2 py-2 font-medium">Ad</th>
                      <th className="px-2 py-2 font-medium">E-posta</th>
                      <th className="px-2 py-2 font-medium">Rol</th>
                      <th className="px-2 py-2 font-medium">Durum</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MOCK_USERS.map((u) => (
                      <tr key={u.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                        <td className="px-2 py-2.5 font-medium">{u.name}</td>
                        <td className="px-2 py-2.5 text-text-2">{u.email}</td>
                        <td className="px-2 py-2.5"><Badge tone="primary">{u.role}</Badge></td>
                        <td className="px-2 py-2.5"><Badge tone={u.active ? "success" : "neutral"}>{u.active ? "Aktif" : "Pasif"}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                    <th className="px-2 py-2 font-medium">Ad</th>
                    <th className="px-2 py-2 font-medium">E-posta</th>
                    <th className="px-2 py-2 font-medium">Rol</th>
                    <th className="px-2 py-2 font-medium">Durum</th>
                    <th className="px-2 py-2 font-medium">Oluşturulma</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                      <td className="px-2 py-2.5 font-medium">{u.full_name}</td>
                      <td className="px-2 py-2.5 text-text-2">{u.email}</td>
                      <td className="px-2 py-2.5"><Badge tone="primary">{u.role}</Badge></td>
                      <td className="px-2 py-2.5"><Badge tone={u.is_active ? "success" : "neutral"}>{u.is_active ? "Aktif" : "Pasif"}</Badge></td>
                      <td className="px-2 py-2.5 font-mono text-text-2">{u.created_at?.split("T")[0] || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <UserCreateModal
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            onSuccess={fetchUsers}
          />
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
        <div className="space-y-4">
          <Card title="Arayüz Dili">
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium">Uygulama Dili</p>
                <p className="text-xs text-text-2">Arayüz dilini değiştirin (Türkçe / English)</p>
              </div>
              <LanguageSwitcher />
            </div>
          </Card>

          <Card title="Genel Yapılandırma">
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {[
                { k: "Tesis Adı", v: "HotelOps Demo Resort" },
                { k: "Para Birimi", v: "TRY (₺)" },
                { k: "Saat Dilimi", v: "Europe/Istanbul (UTC+3)" },
                { k: "Check-in Saati", v: "14:00" },
                { k: "Check-out Saati", v: "12:00" },
                { k: "KDV Oranı", v: "%10 (konaklama)" },
                { k: "API Sürümü", v: "v1.0.0" },
              ].map((row) => (
                <div key={row.k} className="flex items-center justify-between border-b border-line py-2 last:border-0">
                  <dt className="text-sm text-text-2">{row.k}</dt>
                  <dd className="text-sm font-medium">{row.v}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </div>
      )}
    </div>
  );
}
