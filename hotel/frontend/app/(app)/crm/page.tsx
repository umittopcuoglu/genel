"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Guest360 {
  guest_id: string;
  full_name: string;
  email: string;
  lifetime_value: number;
  stay_count: number;
  last_stay: string;
  vip_status: boolean;
  preferred_room_type: string;
  communication_preference: string;
  notes_count: number;
  segments: any[];
}

interface Segment {
  id: string;
  name: string;
  criteria: any;
  is_active: boolean;
  member_count: number;
}

interface Campaign {
  id: string;
  name: string;
  channel: string;
  status: string;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
}

interface Note {
  id: string;
  guest_id: string;
  text: string;
  created_at: string;
}

export default function CRMPage() {
  const [tab, setTab] = useState<"guest360" | "segments" | "campaigns">("guest360");
  const [guest360, setGuest360] = useState<Guest360 | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [guestId, setGuestId] = useState("");
  const [segForm, setSegForm] = useState({ name: "", criteria: '{"is_vip": true}' });
  const [cmpForm, setCmpForm] = useState({ name: "", channel: "email", subject: "" });
  const [noteForm, setNoteForm] = useState({ guest_id: "", text: "" });
  const [error, setError] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const loadGuest360 = () => {
    if (!guestId) return;
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/v1/crm/guests/${guestId}/360`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/v1/crm/guests/${guestId}/notes`, { headers }).then((r) => r.json()),
    ])
      .then(([g, n]) => {
        setGuest360(g);
        setNotes(Array.isArray(n) ? n : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const loadSegments = () => {
    fetch(`${API}/api/v1/crm/segments`, { headers })
      .then((r) => r.json())
      .then((data) => setSegments(Array.isArray(data) ? data : []))
      .catch(() => setSegments([]));
  };

  const loadCampaigns = () => {
    fetch(`${API}/api/v1/crm/campaigns`, { headers })
      .then((r) => r.json())
      .then((data) => setCampaigns(Array.isArray(data) ? data : []))
      .catch(() => setCampaigns([]));
  };

  useEffect(() => {
    if (tab === "segments") loadSegments();
    if (tab === "campaigns") loadCampaigns();
  }, [tab]);

  const createSegment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/crm/segments`, {
        method: "POST",
        headers,
        body: JSON.stringify({ name: segForm.name, criteria: JSON.parse(segForm.criteria) }),
      });
      if (!res.ok) throw new Error("Segment oluşturulamadı");
      loadSegments();
      setSegForm({ name: "", criteria: '{"is_vip": true}' });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const createCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/crm/campaigns`, {
        method: "POST",
        headers,
        body: JSON.stringify(cmpForm),
      });
      if (!res.ok) throw new Error("Kampanya oluşturulamadı");
      loadCampaigns();
      setCmpForm({ name: "", channel: "email", subject: "" });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const sendCampaign = async (id: string) => {
    if (!confirm("Kampanya gönderilsin mi?")) return;
    try {
      await fetch(`${API}/api/v1/crm/campaigns/${id}/send`, { method: "POST", headers });
      loadCampaigns();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const addNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!guestId || !noteForm.text) return;
    setError("");
    try {
      await fetch(`${API}/api/v1/crm/notes`, {
        method: "POST",
        headers,
        body: JSON.stringify({ guest_id: guestId, text: noteForm.text }),
      });
      loadGuest360();
      setNoteForm({ ...noteForm, text: "" });
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="CRM / Guest 360"
        subtitle="Misafir profilleri · Segmentler · Pazarlama kampanyaları"
      />

      <div className="flex gap-2 border-b">
        {[
          ["guest360", "Guest 360"],
          ["segments", "Segmentler"],
          ["campaigns", "Kampanyalar"],
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

      {tab === "guest360" && (
        <>
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Misafir Ara</h3>
            <div className="flex gap-2">
              <input
                placeholder="Misafir UUID girin"
                value={guestId}
                onChange={(e) => setGuestId(e.target.value)}
                className="flex-1 rounded border px-3 py-2"
              />
              <button
                onClick={loadGuest360}
                className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Ara
              </button>
            </div>
          </Card>

          {guest360 && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Card className="p-4">
                  <p className="text-xs uppercase text-slate-500">Ömür Boyu Değeri</p>
                  <p className="text-2xl font-semibold">₺{guest360.lifetime_value.toLocaleString("tr-TR")}</p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs uppercase text-slate-500">Konaklama Sayısı</p>
                  <p className="text-2xl font-semibold">{guest360.stay_count}</p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs uppercase text-slate-500">Son Konaklama</p>
                  <p className="text-sm font-semibold">{guest360.last_stay ? new Date(guest360.last_stay).toLocaleDateString("tr-TR") : "-"}</p>
                </Card>
                <Card className="p-4">
                  <p className="text-xs uppercase text-slate-500">Durum</p>
                  <Badge className={guest360.vip_status ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-700"}>
                    {guest360.vip_status ? "VIP" : "Standart"}
                  </Badge>
                </Card>
              </div>

              <Card className="p-6">
                <h3 className="mb-4 text-lg font-semibold">{guest360.full_name}</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase text-slate-500">E-Posta</p>
                    <p className="font-mono text-sm">{guest360.email}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase text-slate-500">Tercih Edilen Oda Tipi</p>
                    <p className="text-sm">{guest360.preferred_room_type || "-"}</p>
                  </div>
                </div>

                {guest360.segments && guest360.segments.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs uppercase text-slate-500 mb-2">Ait Olduğu Segmentler</p>
                    <div className="flex flex-wrap gap-2">
                      {guest360.segments.map((s, i) => (
                        <Badge key={i} className="bg-blue-100 text-blue-800">
                          {s.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </Card>

              <Card className="p-6">
                <h3 className="mb-4 text-lg font-semibold">Notlar ({guest360.notes_count})</h3>
                <form onSubmit={addNote} className="mb-4 space-y-2">
                  <textarea
                    value={noteForm.text}
                    onChange={(e) => setNoteForm({ ...noteForm, text: e.target.value })}
                    placeholder="Not ekleyin…"
                    className="w-full rounded border px-3 py-2"
                    rows={3}
                  />
                  <button
                    type="submit"
                    className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Not Ekle
                  </button>
                </form>
                <div className="space-y-2">
                  {notes.map((n) => (
                    <div key={n.id} className="rounded border p-3">
                      <p className="text-sm">{n.text}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        {new Date(n.created_at).toLocaleString("tr-TR")}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}
        </>
      )}

      {tab === "segments" && (
        <>
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Yeni Segment</h3>
            <form onSubmit={createSegment} className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="text-sm">Segment Adı *</label>
                <input
                  required
                  value={segForm.name}
                  onChange={(e) => setSegForm({ ...segForm, name: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="text-sm">Kriterler (JSON) *</label>
                <textarea
                  required
                  value={segForm.criteria}
                  onChange={(e) => setSegForm({ ...segForm, criteria: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                  rows={2}
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Oluştur
                </button>
              </div>
            </form>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {segments.map((seg) => (
              <Card key={seg.id} className="p-4">
                <h4 className="font-semibold">{seg.name}</h4>
                <p className="text-xs text-slate-500 mt-1 font-mono">{JSON.stringify(seg.criteria)}</p>
                <div className="mt-3 flex items-center justify-between">
                  <Badge className={seg.is_active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"}>
                    {seg.is_active ? "Aktif" : "Pasif"}
                  </Badge>
                  <span className="text-sm font-semibold">{seg.member_count} üye</span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {tab === "campaigns" && (
        <>
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Yeni Kampanya</h3>
            <form onSubmit={createCampaign} className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="text-sm">Kampanya Adı *</label>
                <input
                  required
                  value={cmpForm.name}
                  onChange={(e) => setCmpForm({ ...cmpForm, name: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                />
              </div>
              <div>
                <label className="text-sm">Kanal *</label>
                <select
                  value={cmpForm.channel}
                  onChange={(e) => setCmpForm({ ...cmpForm, channel: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                >
                  <option value="email">E-Posta</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="push">Push Bildirimi</option>
                </select>
              </div>
              <div>
                <label className="text-sm">Konu *</label>
                <input
                  required
                  value={cmpForm.subject}
                  onChange={(e) => setCmpForm({ ...cmpForm, subject: e.target.value })}
                  className="mt-1 w-full rounded border px-3 py-2"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Oluştur
                </button>
              </div>
            </form>
          </Card>

          <div className="space-y-3">
            {campaigns.map((cmp) => (
              <Card key={cmp.id} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{cmp.name}</h4>
                  <Badge
                    className={
                      cmp.status === "sent"
                        ? "bg-emerald-100 text-emerald-800"
                        : cmp.status === "draft"
                        ? "bg-slate-100 text-slate-700"
                        : "bg-blue-100 text-blue-800"
                    }
                  >
                    {cmp.status}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mb-2">{cmp.channel.toUpperCase()}</p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <p className="text-slate-500">Gönderilen</p>
                    <p className="font-semibold">{cmp.sent_count}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Teslim</p>
                    <p className="font-semibold text-emerald-600">{cmp.delivered_count}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Başarısız</p>
                    <p className="font-semibold text-rose-600">{cmp.failed_count}</p>
                  </div>
                </div>
                {cmp.status === "draft" && (
                  <button
                    onClick={() => sendCampaign(cmp.id)}
                    className="mt-3 w-full rounded bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700"
                  >
                    Gönder
                  </button>
                )}
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
