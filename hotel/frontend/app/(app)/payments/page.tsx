"use client";

import { useState } from "react";
import { RefreshCcw, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingState, MockBanner } from "@/components/ui/DataStates";
import { useApiData } from "@/lib/useApiData";
import { api } from "@/lib/api";
import { MOCK_PAYMENTS, type PaymentTxn } from "@/lib/mock-modules";

const STATUS_TONE: Record<string, string> = {
  succeeded: "bg-emerald-100 text-emerald-700",
  pending: "bg-amber-100 text-amber-700",
  failed: "bg-rose-100 text-rose-700",
  refunded: "bg-slate-100 text-slate-700",
};

export default function PaymentsPage() {
  const {
    data: txns,
    loading,
    usingFallback,
    refetch,
  } = useApiData<PaymentTxn[]>({
    path: "/api/v1/payments",
    fallback: MOCK_PAYMENTS,
  });

  const [form, setForm] = useState({
    amount: "100.00",
    currency: "TRY",
    holder_name: "",
    number: "",
    exp_month: 12,
    exp_year: 2030,
    cvc: "",
    use_3d_secure: false,
  });
  const [msg, setMsg] = useState<string>("");

  async function charge() {
    setMsg("");
    try {
      const body = await api<{ success: boolean; txn: PaymentTxn }>("/api/v1/payments/charge", {
        method: "POST",
        body: JSON.stringify({
          amount: form.amount,
          currency: form.currency,
          use_3d_secure: form.use_3d_secure,
          card: {
            holder_name: form.holder_name,
            number: form.number.replace(/\s/g, ""),
            exp_month: Number(form.exp_month),
            exp_year: Number(form.exp_year),
            cvc: form.cvc,
          },
        }),
      });
      setMsg(body.success ? "Tahsilat basarili" : `${body.txn?.error_message || "Reddedildi"}`);
      refetch();
    } catch {
      setMsg("Backend baglantisi kurulamadi");
    }
  }

  async function doRefund(id: string) {
    try {
      await api("/api/v1/payments/refund", {
        method: "POST",
        body: JSON.stringify({ txn_id: id }),
      });
      refetch();
    } catch {
      setMsg("Iade islemi basarisiz");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Odeme / POS"
        subtitle="Sanal POS tahsilatlari — provider parametrik (iyzico / Stripe / PayTR)"
      />

      {usingFallback && <MockBanner />}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4 p-6">
          <h3 className="text-lg font-semibold">Yeni Tahsilat</h3>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-sm">
              Tutar
              <input
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </label>
            <label className="text-sm">
              Para Birimi
              <select
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              >
                <option>TRY</option>
                <option>EUR</option>
                <option>USD</option>
              </select>
            </label>
            <label className="col-span-2 text-sm">
              Kart Uzerindeki Isim
              <input
                value={form.holder_name}
                onChange={(e) => setForm({ ...form, holder_name: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </label>
            <label className="col-span-2 text-sm">
              Kart Numarasi
              <input
                value={form.number}
                onChange={(e) => setForm({ ...form, number: e.target.value })}
                placeholder="4111 1111 1111 1111"
                className="mt-1 w-full rounded border px-3 py-2 font-mono"
              />
            </label>
            <label className="text-sm">
              Ay
              <input
                type="number"
                value={form.exp_month}
                onChange={(e) => setForm({ ...form, exp_month: Number(e.target.value) })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </label>
            <label className="text-sm">
              Yil
              <input
                type="number"
                value={form.exp_year}
                onChange={(e) => setForm({ ...form, exp_year: Number(e.target.value) })}
                className="mt-1 w-full rounded border px-3 py-2"
              />
            </label>
            <label className="text-sm">
              CVC
              <input
                value={form.cvc}
                onChange={(e) => setForm({ ...form, cvc: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2 font-mono"
              />
            </label>
            <label className="flex items-end gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.use_3d_secure}
                onChange={(e) => setForm({ ...form, use_3d_secure: e.target.checked })}
              />
              <ShieldCheck className="h-4 w-4" /> 3D Secure
            </label>
          </div>
          <button
            onClick={charge}
            className="w-full rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700"
          >
            Tahsilat Yap
          </button>
          {msg && <p className="text-sm">{msg}</p>}
        </Card>

        <Card className="space-y-3 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Son Islemler</h3>
            <button onClick={refetch} className="flex items-center gap-1 text-sm text-slate-500">
              <RefreshCcw className="h-3 w-3" /> Yenile
            </button>
          </div>
          {loading && <LoadingState message="Islemler yukleniyor..." />}
          <div className="max-h-[500px] space-y-2 overflow-auto">
            {txns.map((t) => (
              <div key={t.id} className="rounded-lg border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-500">{t.provider_ref || t.id.slice(0, 8)}</span>
                  <Badge className={STATUS_TONE[t.status] || ""}>{t.status}</Badge>
                </div>
                <div className="mt-1 flex items-center justify-between">
                  <span>
                    {t.kind === "refund" ? "↩ " : ""}
                    {t.amount} {t.currency} · {t.provider}
                    {t.card_last4 && (
                      <span className="ml-2 text-slate-500">
                        {t.card_brand} •••• {t.card_last4}
                      </span>
                    )}
                  </span>
                  {t.kind === "charge" && t.status === "succeeded" && (
                    <button
                      onClick={() => doRefund(t.id)}
                      className="text-xs text-rose-600 hover:underline"
                    >
                      Iade
                    </button>
                  )}
                </div>
                {t.error_message && (
                  <p className="mt-1 text-xs text-rose-600">{t.error_message}</p>
                )}
              </div>
            ))}
            {!loading && txns.length === 0 && (
              <p className="text-sm text-slate-500">Henuz islem yok.</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
