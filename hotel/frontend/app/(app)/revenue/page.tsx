"use client";

import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_TONE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
};

interface Recommendation {
  id: string;
  room_type_id: string;
  date: string;
  recommended_rate: number;
  current_rate: number;
  price_change_percent: number;
  rationale: string;
  confidence_score: number;
  occupancy_forecast: number;
  demand_trend: string;
  competitor_avg_rate?: number;
  status: string;
}

export default function RevenuePage() {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [roomTypes, setRoomTypes] = useState<any[]>([]);
  const [form, setForm] = useState({
    room_type_id: "",
    target_date: new Date().toISOString().slice(0, 10),
    competitor_avg_rate: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/v1/revenue/recommendations`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/v1/front-office/room-types`, { headers }).then((r) => r.json()),
    ])
      .then(([r, rt]) => {
        setRecs(Array.isArray(r) ? r : []);
        setRoomTypes(Array.isArray(rt) ? rt : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, []);

  const handleRecommend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/v1/revenue/recommend`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          room_type_id: form.room_type_id,
          target_date: form.target_date,
          competitor_avg_rate: form.competitor_avg_rate ? parseFloat(form.competitor_avg_rate) : null,
        }),
      });
      if (!res.ok) {
        const e = await res.json();
        throw new Error(e.detail || e.error?.message || "Öneri üretilemedi");
      }
      load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const approve = async (id: string) => {
    await fetch(`${API}/api/v1/revenue/recommendations/${id}/approve`, { method: "POST", headers });
    load();
  };

  const reject = async (id: string) => {
    await fetch(`${API}/api/v1/revenue/recommendations/${id}/reject`, { method: "POST", headers });
    load();
  };

  const pending = recs.filter((r) => r.status === "pending").length;
  const approved = recs.filter((r) => r.status === "approved").length;
  const avgChange =
    recs.length > 0
      ? (recs.reduce((s, r) => s + r.price_change_percent, 0) / recs.length).toFixed(1)
      : "0";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Revenue Management"
        description="Fiyat AI önerileri + doluluk tahmini + onay akışı"
        icon={TrendingUp}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Bekleyen</p>
          <p className="text-2xl font-semibold text-amber-600">{pending}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Onaylanan</p>
          <p className="text-2xl font-semibold text-emerald-600">{approved}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Toplam Öneri</p>
          <p className="text-2xl font-semibold">{recs.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Ort. Fiyat Değişim</p>
          <p className="text-2xl font-semibold">%{avgChange}</p>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="mb-4 text-lg font-semibold">Yeni Fiyat Önerisi Üret</h3>
        {error && <div className="mb-3 rounded bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        <form onSubmit={handleRecommend} className="grid gap-4 md:grid-cols-4">
          <div>
            <label className="text-sm">Oda Tipi *</label>
            <select
              required
              value={form.room_type_id}
              onChange={(e) => setForm({ ...form, room_type_id: e.target.value })}
              className="mt-1 w-full rounded border px-3 py-2"
            >
              <option value="">Seç…</option>
              {roomTypes.map((rt) => (
                <option key={rt.id} value={rt.id}>
                  {rt.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm">Tarih *</label>
            <input
              required
              type="date"
              value={form.target_date}
              onChange={(e) => setForm({ ...form, target_date: e.target.value })}
              className="mt-1 w-full rounded border px-3 py-2"
            />
          </div>
          <div>
            <label className="text-sm">Rakip Ort. Fiyat (₺)</label>
            <input
              type="number"
              step="0.01"
              value={form.competitor_avg_rate}
              onChange={(e) => setForm({ ...form, competitor_avg_rate: e.target.value })}
              className="mt-1 w-full rounded border px-3 py-2"
              placeholder="opsiyonel"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={busy || !form.room_type_id}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-slate-400"
            >
              {busy ? "Üretiliyor…" : "Öneri Üret"}
            </button>
          </div>
        </form>
      </Card>

      <Card className="p-0">
        <div className="border-b p-4">
          <h3 className="text-lg font-semibold">Fiyat Önerileri</h3>
        </div>
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Yükleniyor…</p>
        ) : recs.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">Henüz öneri yok.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Tarih</th>
                  <th className="px-4 py-3">Mevcut</th>
                  <th className="px-4 py-3">Önerilen</th>
                  <th className="px-4 py-3">Değişim</th>
                  <th className="px-4 py-3">Doluluk</th>
                  <th className="px-4 py-3">Trend</th>
                  <th className="px-4 py-3">Güven</th>
                  <th className="px-4 py-3">Durum</th>
                  <th className="px-4 py-3">Aksiyon</th>
                </tr>
              </thead>
              <tbody>
                {recs.map((r) => (
                  <tr key={r.id} className="border-t">
                    <td className="px-4 py-3 font-mono text-xs">{r.date}</td>
                    <td className="px-4 py-3">₺{Number(r.current_rate).toLocaleString("tr-TR")}</td>
                    <td className="px-4 py-3 font-semibold">
                      ₺{Number(r.recommended_rate).toLocaleString("tr-TR")}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`font-medium ${
                          r.price_change_percent > 0 ? "text-emerald-600" : "text-rose-600"
                        }`}
                      >
                        {r.price_change_percent > 0 ? "+" : ""}
                        {r.price_change_percent.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">{(r.occupancy_forecast * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3">
                      <Badge className="bg-slate-100 text-slate-700">{r.demand_trend}</Badge>
                    </td>
                    <td className="px-4 py-3">{(r.confidence_score * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3">
                      <Badge className={STATUS_TONE[r.status] || ""}>{r.status}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {r.status === "pending" && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => approve(r.id)}
                            className="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700"
                          >
                            Onay
                          </button>
                          <button
                            onClick={() => reject(r.id)}
                            className="rounded bg-rose-600 px-2 py-1 text-xs text-white hover:bg-rose-700"
                          >
                            Red
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
