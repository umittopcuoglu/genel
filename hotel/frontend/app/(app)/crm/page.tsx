"use client";

import { useEffect, useState } from "react";
import { Users, Send, Target } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Segment = { id: string; name: string; criteria: any; is_active: boolean };
type Campaign = {
  id: string;
  name: string;
  channel: string;
  status: string;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
};

export default function CRMPage() {
  const [tab, setTab] = useState<"segments" | "campaigns">("segments");
  const [segments, setSegments] = useState<Segment[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [segForm, setSegForm] = useState({ name: "", criteria: '{"is_vip": true}' });
  const [cmpForm, setCmpForm] = useState({
    name: "",
    channel: "email",
    subject: "",
    body: "",
    segment_id: "",
  });

  function authHeaders() {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
    return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
  }

  async function load() {
    const [s, c] = await Promise.all([
      fetch(`${API}/api/v1/crm/segments`, { headers: authHeaders() }),
      fetch(`${API}/api/v1/crm/campaigns`, { headers: authHeaders() }),
    ]);
    if (s.ok) setSegments(await s.json());
    if (c.ok) setCampaigns(await c.json());
  }

  useEffect(() => {
    load();
  }, []);

  async function createSegment() {
    try {
      const criteria = JSON.parse(segForm.criteria || "{}");
      const r = await fetch(`${API}/api/v1/crm/segments`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ name: segForm.name, criteria }),
      });
      if (r.ok) {
        setSegForm({ name: "", criteria: '{"is_vip": true}' });
        load();
      }
    } catch {
      alert("Kriter JSON formatı geçersiz");
    }
  }

  async function preview(id: string) {
    const r = await fetch(`${API}/api/v1/crm/segments/${id}/preview`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (r.ok) {
      const data = await r.json();
      alert(`Eşleşen misafir: ${data.match_count}`);
    }
  }

  async function createCampaign() {
    const r = await fetch(`${API}/api/v1/crm/campaigns`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(cmpForm),
    });
    if (r.ok) {
      setCmpForm({ name: "", channel: "email", subject: "", body: "", segment_id: "" });
      load();
    }
  }

  async function send(id: string) {
    const r = await fetch(`${API}/api/v1/crm/campaigns/${id}/send`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (r.ok) load();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="CRM / Misafir 360"
        description="Misafir profili, segment, kampanya ve iletişim yönetimi"
        icon={Users}
      />

      <div className="flex gap-2">
        <button
          onClick={() => setTab("segments")}
          className={`rounded-lg px-4 py-2 text-sm ${
            tab === "segments" ? "bg-slate-900 text-white" : "bg-slate-100"
          }`}
        >
          <Target className="mr-1 inline h-3 w-3" /> Segmentler ({segments.length})
        </button>
        <button
          onClick={() => setTab("campaigns")}
          className={`rounded-lg px-4 py-2 text-sm ${
            tab === "campaigns" ? "bg-slate-900 text-white" : "bg-slate-100"
          }`}
        >
          <Send className="mr-1 inline h-3 w-3" /> Kampanyalar ({campaigns.length})
        </button>
      </div>

      {tab === "segments" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="space-y-3 p-6">
            <h3 className="text-lg font-semibold">Yeni Segment</h3>
            <input
              placeholder="Segment adı (ör. VIP Misafirler)"
              value={segForm.name}
              onChange={(e) => setSegForm({ ...segForm, name: e.target.value })}
              className="w-full rounded border px-3 py-2"
            />
            <textarea
              value={segForm.criteria}
              onChange={(e) => setSegForm({ ...segForm, criteria: e.target.value })}
              className="w-full rounded border px-3 py-2 font-mono text-sm"
              rows={4}
              placeholder='{"min_stays": 3, "tiers": ["gold","platinum"]}'
            />
            <button
              onClick={createSegment}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2 text-white"
            >
              Oluştur
            </button>
          </Card>
          <Card className="space-y-2 p-6">
            <h3 className="text-lg font-semibold">Mevcut Segmentler</h3>
            {segments.map((s) => (
              <div key={s.id} className="flex items-center justify-between rounded border p-3 text-sm">
                <div>
                  <div className="font-medium">{s.name}</div>
                  <div className="font-mono text-xs text-slate-500">{JSON.stringify(s.criteria)}</div>
                </div>
                <button onClick={() => preview(s.id)} className="text-xs text-blue-600 hover:underline">
                  Önizle
                </button>
              </div>
            ))}
            {segments.length === 0 && <p className="text-sm text-slate-500">Henüz segment yok.</p>}
          </Card>
        </div>
      )}

      {tab === "campaigns" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="space-y-3 p-6">
            <h3 className="text-lg font-semibold">Yeni Kampanya</h3>
            <input
              placeholder="Kampanya adı"
              value={cmpForm.name}
              onChange={(e) => setCmpForm({ ...cmpForm, name: e.target.value })}
              className="w-full rounded border px-3 py-2"
            />
            <div className="grid grid-cols-2 gap-2">
              <select
                value={cmpForm.channel}
                onChange={(e) => setCmpForm({ ...cmpForm, channel: e.target.value })}
                className="rounded border px-3 py-2"
              >
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="push">Push</option>
              </select>
              <select
                value={cmpForm.segment_id}
                onChange={(e) => setCmpForm({ ...cmpForm, segment_id: e.target.value })}
                className="rounded border px-3 py-2"
              >
                <option value="">Segment seçin</option>
                {segments.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <input
              placeholder="Konu (email için)"
              value={cmpForm.subject}
              onChange={(e) => setCmpForm({ ...cmpForm, subject: e.target.value })}
              className="w-full rounded border px-3 py-2"
            />
            <textarea
              placeholder="Mesaj gövdesi"
              value={cmpForm.body}
              onChange={(e) => setCmpForm({ ...cmpForm, body: e.target.value })}
              className="w-full rounded border px-3 py-2"
              rows={4}
            />
            <button
              onClick={createCampaign}
              className="w-full rounded-lg bg-emerald-600 px-4 py-2 text-white"
            >
              Taslak Oluştur
            </button>
          </Card>
          <Card className="space-y-2 p-6">
            <h3 className="text-lg font-semibold">Kampanyalar</h3>
            {campaigns.map((c) => (
              <div key={c.id} className="rounded border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{c.name}</span>
                  <Badge>{c.status}</Badge>
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  Kanal: {c.channel} · Gönderim: {c.sent_count} (✓ {c.delivered_count} / ✕ {c.failed_count})
                </div>
                {c.status === "draft" && (
                  <button
                    onClick={() => send(c.id)}
                    className="mt-2 text-xs text-blue-600 hover:underline"
                  >
                    Gönder
                  </button>
                )}
              </div>
            ))}
            {campaigns.length === 0 && <p className="text-sm text-slate-500">Kampanya yok.</p>}
          </Card>
        </div>
      )}
    </div>
  );
}
