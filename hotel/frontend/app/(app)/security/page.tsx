"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CONSENT_TONE: Record<string, string> = {
  granted: "bg-emerald-100 text-emerald-800",
  revoked: "bg-rose-100 text-rose-800",
};

const DSR_TONE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  in_progress: "bg-blue-100 text-blue-800",
  fulfilled: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
};

const DSR_TYPE_LABEL: Record<string, string> = {
  access: "Veri Erişim",
  erase: "Veri Silme",
  rectify: "Düzeltme",
  portability: "Taşınabilirlik",
};

interface Consent {
  id: string;
  guest_id: string;
  purpose: string;
  text_version: string;
  granted_at: string;
  revoked_at?: string;
  status: string;
}

interface DSR {
  id: string;
  guest_id: string;
  request_type: string;
  status: string;
  notes?: string;
  completed_at?: string;
  created_at: string;
}

export default function SecurityPage() {
  const [tab, setTab] = useState<"consents" | "dsr">("dsr");
  const [requests, setRequests] = useState<DSR[]>([]);
  const [consents, setConsents] = useState<Consent[]>([]);
  const [loading, setLoading] = useState(true);
  const [guestId, setGuestId] = useState("");
  const [form, setForm] = useState({ guest_id: "", purpose: "marketing", text_version: "v1.0" });
  const [dsrForm, setDsrForm] = useState({ guest_id: "", request_type: "access", notes: "" });
  const [error, setError] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const loadDSR = () => {
    setLoading(true);
    fetch(`${API}/api/v1/security/kvkk/requests`, { headers })
      .then((r) => r.json())
      .then((data) => {
        setRequests(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const loadConsents = () => {
    if (!guestId) return;
    fetch(`${API}/api/v1/security/kvkk/guests/${guestId}/consents`, { headers })
      .then((r) => r.json())
      .then((data) => setConsents(Array.isArray(data) ? data : []))
      .catch(() => setConsents([]));
  };

  useEffect(() => {
    if (tab === "dsr") loadDSR();
  }, [tab]);

  const grantConsent = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/security/kvkk/consents`, {
        method: "POST",
        headers,
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Onay verme başarısız");
      setGuestId(form.guest_id);
      loadConsents();
      setForm({ guest_id: "", purpose: "marketing", text_version: "v1.0" });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const revokeConsent = async (id: string) => {
    if (!confirm("Onayı geri çekmek istediğinden emin misin?")) return;
    await fetch(`${API}/api/v1/security/kvkk/consents/${id}/revoke`, { method: "POST", headers });
    loadConsents();
  };

  const createDSR = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/security/kvkk/requests`, {
        method: "POST",
        headers,
        body: JSON.stringify(dsrForm),
      });
      if (!res.ok) throw new Error("Talep oluşturulamadı");
      loadDSR();
      setDsrForm({ guest_id: "", request_type: "access", notes: "" });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const fulfillDSR = async (id: string) => {
    await fetch(`${API}/api/v1/security/kvkk/requests/${id}/fulfill`, { method: "POST", headers });
    loadDSR();
  };

  const dsrByStatus = (status: string) => requests.filter((r) => r.status === status);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Güvenlik & KVKK"
        subtitle="KVKK rıza yönetimi + Veri Sahibi Talepleri (DSR) Kanban"
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Bekleyen Talep</p>
          <p className="text-2xl font-semibold text-amber-600">{dsrByStatus("pending").length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">İşlemde</p>
          <p className="text-2xl font-semibold text-blue-600">{dsrByStatus("in_progress").length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Tamamlanan</p>
          <p className="text-2xl font-semibold text-emerald-600">{dsrByStatus("fulfilled").length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Toplam</p>
          <p className="text-2xl font-semibold">{requests.length}</p>
        </Card>
      </div>

      <div className="flex gap-2 border-b">
        {[
          ["dsr", "DSR Kanban"],
          ["consents", "Rıza Yönetimi"],
        ].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k as any)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === k ? "border-b-2 border-blue-600 text-blue-600" : "text-slate-600"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {error && <div className="rounded bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {tab === "dsr" && (
        <>
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Yeni Veri Sahibi Talebi</h3>
            <form onSubmit={createDSR} className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="text-sm">Misafir ID *</label>
                <input
                  required
                  value={dsrForm.guest_id}
                  onChange={(e) => setDsrForm({ ...dsrForm, guest_id: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                  placeholder="UUID"
                />
              </div>
              <div>
                <label className="text-sm">Talep Türü *</label>
                <select
                  value={dsrForm.request_type}
                  onChange={(e) => setDsrForm({ ...dsrForm, request_type: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                >
                  <option value="access">Veri Erişim</option>
                  <option value="erase">Veri Silme</option>
                  <option value="rectify">Düzeltme</option>
                  <option value="portability">Taşınabilirlik</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-sm">Notlar</label>
                <input
                  value={dsrForm.notes}
                  onChange={(e) => setDsrForm({ ...dsrForm, notes: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                />
              </div>
              <div className="md:col-span-4">
                <button
                  type="submit"
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Talep Oluştur
                </button>
              </div>
            </form>
          </Card>

          <div className="grid gap-4 md:grid-cols-4">
            {[
              ["pending", "Bekleyen"],
              ["in_progress", "İşlemde"],
              ["fulfilled", "Tamamlandı"],
              ["rejected", "Reddedildi"],
            ].map(([status, label]) => (
              <Card key={status} className="p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h4 className="text-sm font-semibold">{label}</h4>
                  <Badge className={DSR_TONE[status as string]}>{dsrByStatus(status as string).length}</Badge>
                </div>
                <div className="space-y-2">
                  {loading ? (
                    <p className="text-xs text-slate-500">Yükleniyor…</p>
                  ) : dsrByStatus(status as string).length === 0 ? (
                    <p className="text-xs text-slate-400">—</p>
                  ) : (
                    dsrByStatus(status as string).map((r) => (
                      <div key={r.id} className="rounded border p-3 text-xs">
                        <div className="mb-1 flex items-center justify-between">
                          <Badge className="bg-slate-100 text-slate-700">
                            {DSR_TYPE_LABEL[r.request_type] || r.request_type}
                          </Badge>
                          <span className="text-slate-400">
                            {new Date(r.created_at).toLocaleDateString("tr-TR")}
                          </span>
                        </div>
                        <p className="font-mono text-[10px] text-slate-500">
                          {r.guest_id.slice(0, 8)}…
                        </p>
                        {r.notes && <p className="mt-2 text-slate-600">{r.notes}</p>}
                        {status === "pending" && (
                          <button
                            onClick={() => fulfillDSR(r.id)}
                            className="mt-2 w-full rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700"
                          >
                            Tamamla
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {tab === "consents" && (
        <>
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Onay Ver</h3>
            <form onSubmit={grantConsent} className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="text-sm">Misafir ID *</label>
                <input
                  required
                  value={form.guest_id}
                  onChange={(e) => setForm({ ...form, guest_id: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                  placeholder="UUID"
                />
              </div>
              <div>
                <label className="text-sm">Amaç *</label>
                <select
                  value={form.purpose}
                  onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                >
                  <option value="marketing">Pazarlama</option>
                  <option value="profiling">Profilleme</option>
                  <option value="analytics">Analitik</option>
                  <option value="newsletter">Bülten</option>
                </select>
              </div>
              <div>
                <label className="text-sm">Metin Versiyonu</label>
                <input
                  value={form.text_version}
                  onChange={(e) => setForm({ ...form, text_version: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Onay Ver
                </button>
              </div>
            </form>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center gap-2">
              <input
                placeholder="Misafir ID ile ara"
                value={guestId}
                onChange={(e) => setGuestId(e.target.value)}
                className="flex-1 rounded border px-3 py-2"
              />
              <button
                onClick={loadConsents}
                className="rounded bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              >
                Ara
              </button>
            </div>
            {consents.length === 0 ? (
              <p className="text-sm text-slate-500">Onay kaydı yok.</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Amaç</th>
                    <th className="px-3 py-2">Metin</th>
                    <th className="px-3 py-2">Verme Tarihi</th>
                    <th className="px-3 py-2">Durum</th>
                    <th className="px-3 py-2">Aksiyon</th>
                  </tr>
                </thead>
                <tbody>
                  {consents.map((c) => (
                    <tr key={c.id} className="border-t">
                      <td className="px-3 py-2">{c.purpose}</td>
                      <td className="px-3 py-2 font-mono text-xs">{c.text_version}</td>
                      <td className="px-3 py-2 text-xs">
                        {c.granted_at ? new Date(c.granted_at).toLocaleString("tr-TR") : "-"}
                      </td>
                      <td className="px-3 py-2">
                        <Badge className={CONSENT_TONE[c.status] || ""}>{c.status}</Badge>
                      </td>
                      <td className="px-3 py-2">
                        {c.status === "granted" && (
                          <button
                            onClick={() => revokeConsent(c.id)}
                            className="rounded bg-rose-100 px-2 py-1 text-xs text-rose-700 hover:bg-rose-200"
                          >
                            Geri Çek
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
