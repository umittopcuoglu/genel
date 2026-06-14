"use client";

import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { MOCK_USERS, ROLES } from "@/lib/mock-modules";
import { UserCreateModal } from "@/components/UserCreateModal";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTranslation } from "@/lib/i18n";

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
  const { t } = useTranslation();
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
      <PageHeader title={t("settings.title")} subtitle={t("settings.subtitle")} mock={false} />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[
            { id: "users", labelKey: "settings.users" },
            { id: "roles", labelKey: "settings.roles" },
            { id: "general", labelKey: "settings.general" },
          ].map((item) => (
            <button
              key={item.id}
              role="tab"
              aria-selected={tab === item.id}
              onClick={() => setTab(item.id as typeof tab)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === item.id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
            >
              {t(item.labelKey)}
            </button>
          ))}
        </div>
      </div>

      {tab === "users" && (
        <Card
          title={t("settings.users")}
          action={
            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-white hover:opacity-90"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden /> {t("settings.newUser")}
            </button>
          }
        >
          <div className="overflow-x-auto">
            {loadingUsers ? (
              <div className="py-8 text-center text-text-2 text-sm">{t("settings.loadingUsers")}</div>
            ) : users.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-text-2 text-sm mb-3">{t("settings.noUsersYet")}</p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                      <th className="px-2 py-2 font-medium">{t("common.name")}</th>
                      <th className="px-2 py-2 font-medium">{t("settings.userEmail")}</th>
                      <th className="px-2 py-2 font-medium">{t("settings.userRole")}</th>
                      <th className="px-2 py-2 font-medium">{t("common.status")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {MOCK_USERS.map((u) => (
                      <tr key={u.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                        <td className="px-2 py-2.5 font-medium">{u.name}</td>
                        <td className="px-2 py-2.5 text-text-2">{u.email}</td>
                        <td className="px-2 py-2.5"><Badge tone="primary">{u.role}</Badge></td>
                        <td className="px-2 py-2.5"><Badge tone={u.active ? "success" : "neutral"}>{u.active ? t("settings.userActive") : t("settings.userInactive")}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                    <th className="px-2 py-2 font-medium">{t("common.name")}</th>
                    <th className="px-2 py-2 font-medium">{t("settings.userEmail")}</th>
                    <th className="px-2 py-2 font-medium">{t("settings.userRole")}</th>
                    <th className="px-2 py-2 font-medium">{t("common.status")}</th>
                    <th className="px-2 py-2 font-medium">{t("settings.userCreated")}</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                      <td className="px-2 py-2.5 font-medium">{u.full_name}</td>
                      <td className="px-2 py-2.5 text-text-2">{u.email}</td>
                      <td className="px-2 py-2.5"><Badge tone="primary">{u.role}</Badge></td>
                      <td className="px-2 py-2.5"><Badge tone={u.is_active ? "success" : "neutral"}>{u.is_active ? t("settings.userActive") : t("settings.userInactive")}</Badge></td>
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
          <Card title={t("settings.uiLanguage")}>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium">{t("settings.uiLanguage")}</p>
                <p className="text-xs text-text-2">{t("settings.uiLanguageDesc")}</p>
              </div>
              <LanguageSwitcher />
            </div>
          </Card>

          <Card title={t("settings.general")}>
            <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {[
                { k: t("settings.facilityName"), v: "HotelOps Demo Resort" },
                { k: t("settings.currency"), v: "TRY (₺)" },
                { k: t("settings.timezone"), v: "Europe/Istanbul (UTC+3)" },
                { k: t("settings.checkinTime"), v: "14:00" },
                { k: t("settings.checkoutTime"), v: "12:00" },
                { k: t("settings.vatRate"), v: "%10" },
                { k: t("settings.apiVersion"), v: "v1.0.0" },
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
