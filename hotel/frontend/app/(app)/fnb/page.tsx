"use client";

import { useEffect, useState } from "react";
import { UtensilsCrossed } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const tl = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

interface Outlet {
  id: string;
  name: string;
  outlet_type: string;
  enabled: boolean;
}

interface MenuItem {
  id: string;
  name: string;
  price: number;
  item_type: string;
}

interface CheckItem {
  item_id: string;
  quantity: number;
  price: number;
}

interface Check {
  id: string;
  outlet_id: string;
  room_id?: string;
  check_number: string;
  status: string;
  subtotal: number;
  kdv_amount: number;
  total_amount: number;
  items?: CheckItem[];
  created_at: string;
}

export default function FnbPage() {
  const [tab, setTab] = useState<"outlets" | "checks">("checks");
  const [outlets, setOutlets] = useState<Outlet[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOutlet, setSelectedOutlet] = useState("");
  const [checkForm, setCheckForm] = useState({ room_id: "", outlet_id: "" });
  const [itemForm, setItemForm] = useState({ item_id: "", quantity: 1 });
  const [currentCheck, setCurrentCheck] = useState<Check | null>(null);
  const [error, setError] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/v1/fnb/outlets`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/v1/fnb/checks`, { headers }).then((r) => r.json()),
    ])
      .then(([o, c]) => {
        setOutlets(Array.isArray(o) ? o : []);
        setChecks(Array.isArray(c) ? c : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const loadMenu = (outletId: string) => {
    if (!outletId) return;
    fetch(`${API}/api/v1/fnb/outlets/${outletId}/menu`, { headers })
      .then((r) => r.json())
      .then((data) => setMenuItems(Array.isArray(data) ? data : []))
      .catch(() => setMenuItems([]));
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (selectedOutlet) {
      loadMenu(selectedOutlet);
      setCheckForm({ ...checkForm, outlet_id: selectedOutlet });
    }
  }, [selectedOutlet]);

  const createCheck = async () => {
    if (!checkForm.outlet_id) {
      setError("Satış noktası seçin");
      return;
    }
    setError("");
    try {
      const res = await fetch(`${API}/api/v1/fnb/checks`, {
        method: "POST",
        headers,
        body: JSON.stringify(checkForm),
      });
      if (!res.ok) throw new Error("Adisyon oluşturulamadı");
      const data = await res.json();
      setCurrentCheck(data);
      setCheckForm({ room_id: "", outlet_id: "" });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const addItem = async () => {
    if (!currentCheck || !itemForm.item_id) {
      setError("Adisyon ve ürün seçin");
      return;
    }
    try {
      const res = await fetch(`${API}/api/v1/fnb/checks/${currentCheck.id}/items`, {
        method: "POST",
        headers,
        body: JSON.stringify({ item_id: itemForm.item_id, quantity: itemForm.quantity }),
      });
      if (!res.ok) throw new Error("Ürün eklenemedi");
      const data = await res.json();
      setCurrentCheck(data);
      setItemForm({ item_id: "", quantity: 1 });
    } catch (err: any) {
      setError(err.message);
    }
  };

  const postToFolio = async (checkId: string) => {
    try {
      const res = await fetch(`${API}/api/v1/fnb/checks/${checkId}/post-to-folio`, {
        method: "POST",
        headers,
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Fatura yazamadı");
      load();
      setCurrentCheck(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const settleCash = async (checkId: string) => {
    try {
      await fetch(`${API}/api/v1/fnb/checks/${checkId}/settle-cash`, {
        method: "POST",
        headers,
        body: JSON.stringify({}),
      });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const voidCheck = async (checkId: string) => {
    if (!confirm("Adisyonu iptal etmek istediğinden emin misin?")) return;
    try {
      await fetch(`${API}/api/v1/fnb/checks/${checkId}/void`, {
        method: "POST",
        headers,
        body: JSON.stringify({}),
      });
      load();
      setCurrentCheck(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const openCount = checks.filter((c) => c.status === "open").length;
  const todayTotal = checks.reduce((s, c) => s + c.total_amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="F&B / POS"
        subtitle={`${outlets.length} satış noktası · Adisyon yönetimi`}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Bugün F&B Geliri</p>
          <p className="text-2xl font-semibold text-emerald-600">{tl(todayTotal)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Açık Adisyon</p>
          <p className="text-2xl font-semibold text-amber-600">{openCount}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Satış Noktası</p>
          <p className="text-2xl font-semibold">{outlets.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Menü Ürünü</p>
          <p className="text-2xl font-semibold">{menuItems.length}</p>
        </Card>
      </div>

      <div className="flex gap-2 border-b">
        {[
          ["checks", "Adisyonlar"],
          ["outlets", "Satış Noktaları"],
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

      {tab === "checks" && (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Card className="p-6">
                <h3 className="mb-4 text-lg font-semibold">Adisyonlar</h3>
                {loading ? (
                  <p className="text-sm text-slate-500">Yükleniyor…</p>
                ) : checks.length === 0 ? (
                  <p className="text-sm text-slate-500">Adisyon yok.</p>
                ) : (
                  <div className="space-y-3">
                    {checks.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => setCurrentCheck(c)}
                        className={`cursor-pointer rounded border p-4 ${
                          currentCheck?.id === c.id ? "border-blue-500 bg-blue-50" : "hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-sm font-semibold">{c.check_number}</span>
                          <Badge
                            className={
                              c.status === "open"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-emerald-100 text-emerald-800"
                            }
                          >
                            {c.status}
                          </Badge>
                        </div>
                        {c.room_id && <p className="text-xs text-slate-500">Oda {c.room_id}</p>}
                        <p className="text-sm font-semibold text-slate-900">{tl(c.total_amount)}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>

            <Card className="p-6">
              <h3 className="mb-4 text-lg font-semibold">Yeni Adisyon</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-sm">Satış Noktası *</label>
                  <select
                    value={selectedOutlet}
                    onChange={(e) => setSelectedOutlet(e.target.value)}
                    className="mt-1 w-full rounded border px-3 py-2"
                  >
                    <option value="">Seç…</option>
                    {outlets.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm">Oda No (İsteğe Bağlı)</label>
                  <input
                    type="text"
                    value={checkForm.room_id}
                    onChange={(e) => setCheckForm({ ...checkForm, room_id: e.target.value })}
                    className="mt-1 w-full rounded border px-3 py-2"
                    placeholder="201"
                  />
                </div>
                <button
                  onClick={createCheck}
                  className="w-full rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Adisyon Aç
                </button>
              </div>
            </Card>
          </div>

          {currentCheck && (
            <Card className="p-6">
              <h3 className="mb-4 text-lg font-semibold">Adisyon #{currentCheck.check_number}</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm">Ürün Ekle</label>
                  <div className="mt-2 grid gap-2 md:grid-cols-4">
                    <select
                      value={itemForm.item_id}
                      onChange={(e) => setItemForm({ ...itemForm, item_id: e.target.value })}
                      className="rounded border px-3 py-2"
                    >
                      <option value="">Ürün Seç</option>
                      {menuItems.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({tl(m.price)})
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="1"
                      value={itemForm.quantity}
                      onChange={(e) => setItemForm({ ...itemForm, quantity: parseInt(e.target.value) || 1 })}
                      className="rounded border px-3 py-2"
                    />
                    <button
                      onClick={addItem}
                      className="rounded bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                    >
                      Ekle
                    </button>
                  </div>
                </div>

                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left">Ürün</th>
                      <th className="px-3 py-2 text-right">Fiyat</th>
                      <th className="px-3 py-2 text-right">Adet</th>
                      <th className="px-3 py-2 text-right">Toplam</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentCheck.items?.map((item) => {
                      const product = menuItems.find((m) => m.id === item.item_id);
                      return (
                        <tr key={item.item_id} className="border-t">
                          <td className="px-3 py-2">{product?.name}</td>
                          <td className="px-3 py-2 text-right">{tl(item.price)}</td>
                          <td className="px-3 py-2 text-right">{item.quantity}</td>
                          <td className="px-3 py-2 text-right font-semibold">
                            {tl(item.price * item.quantity)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                <div className="space-y-2 border-t pt-4">
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>{tl(currentCheck.subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>KDV:</span>
                    <span>{tl(currentCheck.kdv_amount)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2 font-semibold">
                    <span>Toplam:</span>
                    <span>{tl(currentCheck.total_amount)}</span>
                  </div>
                </div>

                <div className="grid gap-2 md:grid-cols-3">
                  {currentCheck.status === "open" && (
                    <>
                      <button
                        onClick={() => postToFolio(currentCheck.id)}
                        className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
                      >
                        Fatura Yaz
                      </button>
                      <button
                        onClick={() => settleCash(currentCheck.id)}
                        className="rounded bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                      >
                        Nakit Tahsil
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => voidCheck(currentCheck.id)}
                    className="rounded bg-rose-600 px-3 py-2 text-sm font-medium text-white hover:bg-rose-700"
                  >
                    İptal
                  </button>
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      {tab === "outlets" && (
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Satış Noktaları</h3>
          {outlets.length === 0 ? (
            <p className="text-sm text-slate-500">Satış noktası yok.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {outlets.map((o) => (
                <div key={o.id} className="rounded border p-4">
                  <h4 className="font-semibold">{o.name}</h4>
                  <p className="text-xs text-slate-500 mt-1">{o.outlet_type}</p>
                  <Badge className={o.enabled ? "bg-emerald-100 text-emerald-800 mt-2" : "bg-rose-100 text-rose-800 mt-2"}>
                    {o.enabled ? "Aktif" : "Kapalı"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
