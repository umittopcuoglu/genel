"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function WhatsAppPage() {
  const [form, setForm] = useState({ to_phone: "", text: "" });
  const [result, setResult] = useState<any>(null);
  const [sending, setSending] = useState(false);

  async function send() {
    setSending(true);
    setResult(null);
    const token = localStorage.getItem("token");
    try {
      const r = await fetch(`${API}/api/v1/whatsapp/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      const body = await r.json();
      setResult({ ok: r.ok, body });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="WhatsApp"
        subtitle="Meta Business Cloud API — misafirlere doğrudan mesaj gönderin"
      />

      <Card className="max-w-2xl space-y-4 p-6">
        <h3 className="text-lg font-semibold">Tek Yönlü Mesaj</h3>
        <label className="block text-sm">
          Telefon (E.164: +90...)
          <input
            value={form.to_phone}
            onChange={(e) => setForm({ ...form, to_phone: e.target.value })}
            placeholder="+905551112233"
            className="mt-1 w-full rounded border px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          Mesaj
          <textarea
            value={form.text}
            onChange={(e) => setForm({ ...form, text: e.target.value })}
            rows={4}
            className="mt-1 w-full rounded border px-3 py-2"
          />
        </label>
        <button
          onClick={send}
          disabled={sending || !form.to_phone || !form.text}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          {sending ? "Gönderiliyor..." : "Gönder"}
        </button>
        {result && (
          <div
            className={`rounded border p-3 text-sm ${
              result.ok ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"
            }`}
          >
            {result.ok ? (
              <span>
                ✓ Gönderildi (ref: <code>{result.body.external_ref}</code>)
              </span>
            ) : (
              <span>✕ {result.body.detail || result.body.error?.message}</span>
            )}
          </div>
        )}
        <p className="text-xs text-slate-500">
          Not: Entegrasyon ayarlarında <code>whatsapp</code> kaydı etkin olmalı. Şu an mock modda — gerçek
          gönderim için Meta access token sağlandığında otomatik canlıya geçer.
        </p>
      </Card>
    </div>
  );
}
