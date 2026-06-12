"use client";

import { useEffect, useState } from "react";
import { Receipt } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_TONE: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  sent: "bg-blue-100 text-blue-700",
  accepted: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
  cancelled: "bg-amber-100 text-amber-700",
};

interface Invoice {
  id: string;
  invoice_number: string;
  invoice_date: string;
  customer_name: string;
  customer_email: string;
  customer_tax_id?: string;
  subtotal: number;
  kdv_amount: number;
  total_amount: number;
  einvoice_status: string;
  gib_error_message?: string;
  created_at: string;
}

export default function EInvoicePage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [xmlModal, setXmlModal] = useState<{ open: boolean; number: string; xml: string }>({
    open: false,
    number: "",
    xml: "",
  });
  const [form, setForm] = useState({
    customer_name: "",
    customer_email: "",
    customer_tax_id: "",
    subtotal: "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

  const load = () => {
    setLoading(true);
    fetch(`${API}/api/v1/einvoice`, { headers })
      .then((r) => r.json())
      .then((data) => {
        setInvoices(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/v1/einvoice`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          customer_name: form.customer_name,
          customer_email: form.customer_email,
          customer_tax_id: form.customer_tax_id || null,
          subtotal: parseFloat(form.subtotal),
        }),
      });
      if (!res.ok) {
        const e = await res.json();
        throw new Error(e.detail || e.error?.message || "Fatura oluşturulamadı");
      }
      setShowForm(false);
      setForm({ customer_name: "", customer_email: "", customer_tax_id: "", subtotal: "" });
      load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const sendToGib = async (id: string) => {
    if (!confirm("Fatura GİB'e gönderilsin mi?")) return;
    await fetch(`${API}/api/v1/einvoice/${id}/send`, { method: "POST", headers });
    load();
  };

  const cancelInvoice = async (id: string) => {
    if (!confirm("Fatura iptal edilsin mi?")) return;
    await fetch(`${API}/api/v1/einvoice/${id}/cancel`, { method: "POST", headers });
    load();
  };

  const showXml = async (id: string, num: string) => {
    const res = await fetch(`${API}/api/v1/einvoice/${id}/xml`, { headers });
    const data = await res.json();
    setXmlModal({ open: true, number: num, xml: data.xml || "XML henüz oluşturulmamış" });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="GİB e-Fatura"
        description="Foriba/Logo/Uyumsoft/İzibiz entegratörleri ile e-fatura yönetimi"
        icon={Receipt}
      />

      <div className="flex justify-end">
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          {showForm ? "İptal" : "+ Yeni Fatura"}
        </button>
      </div>

      {showForm && (
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Yeni Fatura</h3>
          {error && <div className="mb-3 rounded bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
          <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm">Müşteri Adı *</label>
              <input
                required
                value={form.customer_name}
                onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </div>
            <div>
              <label className="text-sm">E-Posta *</label>
              <input
                required
                type="email"
                value={form.customer_email}
                onChange={(e) => setForm({ ...form, customer_email: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </div>
            <div>
              <label className="text-sm">Vergi No / TCKN</label>
              <input
                value={form.customer_tax_id}
                onChange={(e) => setForm({ ...form, customer_tax_id: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </div>
            <div>
              <label className="text-sm">Tutar (KDV Hariç) *</label>
              <input
                required
                type="number"
                step="0.01"
                min="0"
                value={form.subtotal}
                onChange={(e) => setForm({ ...form, subtotal: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </div>
            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={busy}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:bg-slate-400"
              >
                {busy ? "Oluşturuluyor..." : "Oluştur"}
              </button>
            </div>
          </form>
        </Card>
      )}

      <Card className="p-0">
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Yükleniyor…</p>
        ) : invoices.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">Henüz fatura yok.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">No</th>
                  <th className="px-4 py-3">Müşteri</th>
                  <th className="px-4 py-3">Tutar</th>
                  <th className="px-4 py-3">KDV</th>
                  <th className="px-4 py-3">Toplam</th>
                  <th className="px-4 py-3">Durum</th>
                  <th className="px-4 py-3">Aksiyon</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} className="border-t">
                    <td className="px-4 py-3 font-mono text-xs">{inv.invoice_number}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{inv.customer_name}</div>
                      <div className="text-xs text-slate-500">{inv.customer_email}</div>
                    </td>
                    <td className="px-4 py-3">₺{Number(inv.subtotal).toLocaleString("tr-TR")}</td>
                    <td className="px-4 py-3">₺{Number(inv.kdv_amount).toLocaleString("tr-TR")}</td>
                    <td className="px-4 py-3 font-medium">
                      ₺{Number(inv.total_amount).toLocaleString("tr-TR")}
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={STATUS_TONE[inv.einvoice_status] || ""}>
                        {inv.einvoice_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {inv.einvoice_status === "draft" && (
                          <button
                            onClick={() => sendToGib(inv.id)}
                            className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700"
                          >
                            Gönder
                          </button>
                        )}
                        <button
                          onClick={() => showXml(inv.id, inv.invoice_number)}
                          className="rounded border px-2 py-1 text-xs hover:bg-slate-50"
                        >
                          XML
                        </button>
                        {inv.einvoice_status !== "cancelled" && (
                          <button
                            onClick={() => cancelInvoice(inv.id)}
                            className="rounded bg-rose-100 px-2 py-1 text-xs text-rose-700 hover:bg-rose-200"
                          >
                            İptal
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {xmlModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[80vh] w-full max-w-3xl overflow-auto rounded-lg bg-white p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">XML — {xmlModal.number}</h3>
              <button
                onClick={() => setXmlModal({ open: false, number: "", xml: "" })}
                className="text-slate-500 hover:text-slate-900"
              >
                ✕
              </button>
            </div>
            <pre className="overflow-auto rounded bg-slate-900 p-4 text-xs text-emerald-300">
              {xmlModal.xml}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
