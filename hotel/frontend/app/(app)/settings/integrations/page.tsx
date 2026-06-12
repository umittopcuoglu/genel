"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  CreditCard,
  FileText,
  Globe,
  Lightbulb,
  Loader2,
  MessageCircle,
  Plug,
  Plus,
  Share2,
  Trash2,
  XCircle,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { api } from "@/lib/api";

/**
 * Entegrasyon Ayarları — admin (superadmin/manager) dış entegrasyon
 * parametrelerini çalışma zamanında girer; "Bağlantıyı Test Et" canlı kontrol yapar.
 * Backend: /api/v1/integrations (parametreler şifreli saklanır, yanıtta maskeli).
 */

type ParamSpec = {
  key: string;
  label: string;
  type: "text" | "secret" | "url" | "number" | "select" | "boolean";
  options?: string[];
  required?: boolean;
};

type Integration = {
  id: string;
  integration_type: string;
  name: string;
  enabled: boolean;
  params: Record<string, any>;
  last_test_at: string | null;
  last_test_ok: boolean | null;
  last_test_message: string | null;
};

const TYPE_META: Record<string, { label: string; icon: any; desc: string }> = {
  gib_einvoice: { label: "GİB e-Fatura", icon: FileText, desc: "Entegratör üzerinden e-Fatura/e-Arşiv" },
  ota_channel: { label: "OTA Kanalı", icon: Share2, desc: "Booking, Expedia, Airbnb…" },
  gds: { label: "GDS", icon: Globe, desc: "Amadeus / Sabre / Travelport" },
  whatsapp: { label: "WhatsApp Business", icon: MessageCircle, desc: "GuestAI chatbot kanalı" },
  payment_gateway: { label: "Ödeme Altyapısı", icon: CreditCard, desc: "iyzico / Stripe / PayTR — booking engine tahsilatı" },
  iot: { label: "IoT / Akıllı Oda", icon: Lightbulb, desc: "MQTT broker — TCP/IP üzerinden" },
};

export default function IntegrationsPage() {
  const [specs, setSpecs] = useState<Record<string, ParamSpec[]>>({});
  const [items, setItems] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null); // açık form: integration_type

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sp, list] = await Promise.all([
        api<Record<string, ParamSpec[]>>("/api/v1/integrations/specs"),
        api<Integration[]>("/api/v1/integrations"),
      ]);
      setSpecs(sp);
      setItems(list);
    } catch (e: any) {
      setError(
        e?.status === 403
          ? "Bu sayfa için superadmin/manager yetkisi gerekir."
          : "Backend'e ulaşılamadı — sunucunun çalıştığından emin olun (http://localhost:8000)."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Entegrasyon Ayarları"
        subtitle="Dış servisleri parametrelerle tanımlayın, tek tıkla bağlantıyı doğrulayın"
        mock={false}
      />

      {error && (
        <div className="rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning">
          {error}
        </div>
      )}

      {loading ? (
        <div className="stagger grid gap-4 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-40" />
          ))}
        </div>
      ) : (
        <div className="stagger grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Object.entries(TYPE_META).map(([type, meta]) => (
            <TypeCard
              key={type}
              type={type}
              meta={meta}
              specs={specs[type] ?? []}
              items={items.filter((i) => i.integration_type === type)}
              creating={creating === type}
              onCreate={() => setCreating(creating === type ? null : type)}
              onChanged={load}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TypeCard({
  type,
  meta,
  specs,
  items,
  creating,
  onCreate,
  onChanged,
}: {
  type: string;
  meta: { label: string; icon: any; desc: string };
  specs: ParamSpec[];
  items: Integration[];
  creating: boolean;
  onCreate: () => void;
  onChanged: () => void;
}) {
  const Icon = meta.icon;
  return (
    <Card
      title={meta.label}
      action={
        <button onClick={onCreate} className="btn-navy !px-2.5 !py-1 text-xs" aria-label={`${meta.label} ekle`}>
          <Plus className="h-3.5 w-3.5" aria-hidden /> Ekle
        </button>
      }
    >
      <div className="mb-3 flex items-center gap-2 text-xs text-text-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/12">
          <Icon className="h-4 w-4 text-accent" aria-hidden />
        </span>
        {meta.desc}
      </div>

      {creating && <CreateForm type={type} specs={specs} onDone={onChanged} />}

      {items.length === 0 && !creating && (
        <div className="rounded-xl border border-dashed border-line p-5 text-center text-xs text-text-2">
          <Plug className="mx-auto mb-1.5 h-4 w-4" aria-hidden />
          Henüz tanımlı değil — &quot;Ekle&quot; ile parametre girin.
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <IntegrationRow key={item.id} item={item} specs={specs} onChanged={onChanged} />
        ))}
      </div>
    </Card>
  );
}

function CreateForm({ type, specs, onDone }: { type: string; specs: ParamSpec[]; onDone: () => void }) {
  const [name, setName] = useState("");
  const [params, setParams] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setErr(null);
    try {
      await api("/api/v1/integrations", {
        method: "POST",
        body: JSON.stringify({ integration_type: type, name: name || "Yeni bağlantı", params }),
      });
      onDone();
    } catch (e: any) {
      setErr(e?.message ?? "Kaydedilemedi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mb-4 space-y-2.5 rounded-xl border border-accent/25 bg-accent/[0.04] p-3.5">
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Bağlantı adı (ör. Booking.com — Ana Otel)"
        className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none transition-all focus:border-accent/60"
      />
      {specs.map((spec) => (
        <ParamInput key={spec.key} spec={spec} value={params[spec.key]} onChange={(v) => setParams((p) => ({ ...p, [spec.key]: v }))} />
      ))}
      {err && <p className="text-xs text-danger">{err}</p>}
      <button onClick={save} disabled={saving} className="btn-gold w-full !py-2 text-xs disabled:opacity-60">
        {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : "Kaydet"}
      </button>
    </div>
  );
}

function ParamInput({ spec, value, onChange }: { spec: ParamSpec; value: any; onChange: (v: any) => void }) {
  const base =
    "w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none transition-all focus:border-accent/60";
  if (spec.type === "select") {
    return (
      <label className="block text-xs text-text-2">
        {spec.label} {spec.required && <span className="text-danger">*</span>}
        <select value={value ?? ""} onChange={(e) => onChange(e.target.value)} className={`${base} mt-1`}>
          <option value="">Seçin…</option>
          {spec.options?.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </label>
    );
  }
  if (spec.type === "boolean") {
    return (
      <label className="flex items-center gap-2 text-xs text-text-2">
        <input type="checkbox" checked={!!value} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 accent-[#c0984a]" />
        {spec.label}
      </label>
    );
  }
  return (
    <label className="block text-xs text-text-2">
      {spec.label} {spec.required && <span className="text-danger">*</span>}
      <input
        type={spec.type === "secret" ? "password" : spec.type === "number" ? "number" : "text"}
        value={value ?? ""}
        onChange={(e) => onChange(spec.type === "number" ? Number(e.target.value) : e.target.value)}
        className={`${base} mt-1`}
      />
    </label>
  );
}

function IntegrationRow({ item, specs, onChanged }: { item: Integration; specs: ParamSpec[]; onChanged: () => void }) {
  const [testing, setTesting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(
    item.last_test_ok === null ? null : { ok: !!item.last_test_ok, message: item.last_test_message ?? "" }
  );

  async function runTest() {
    setTesting(true);
    try {
      const r = await api<{ ok: boolean; message: string }>(`/api/v1/integrations/${item.id}/test`, { method: "POST" });
      setResult(r);
    } catch {
      setResult({ ok: false, message: "Test isteği başarısız." });
    } finally {
      setTesting(false);
    }
  }

  async function toggle() {
    setBusy(true);
    try {
      await api(`/api/v1/integrations/${item.id}`, { method: "PATCH", body: JSON.stringify({ enabled: !item.enabled }) });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!confirm(`"${item.name}" silinsin mi?`)) return;
    setBusy(true);
    try {
      await api(`/api/v1/integrations/${item.id}`, { method: "DELETE" });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-line p-3.5 transition-colors duration-200 hover:border-accent/30">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{item.name}</div>
          <div className="mt-0.5 flex items-center gap-1.5">
            <Badge tone={item.enabled ? "success" : "neutral"}>{item.enabled ? "Aktif" : "Pasif"}</Badge>
            {result &&
              (result.ok ? (
                <Badge tone="success">Bağlantı OK</Badge>
              ) : (
                <Badge tone="danger">Bağlantı hatası</Badge>
              ))}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <button onClick={toggle} disabled={busy} className="btn-navy !px-2.5 !py-1 text-xs disabled:opacity-50">
            {item.enabled ? "Durdur" : "Etkinleştir"}
          </button>
          <button
            onClick={remove}
            disabled={busy}
            aria-label="Sil"
            className="rounded-lg border border-line p-1.5 text-text-2 transition-colors hover:border-danger/40 hover:text-danger disabled:opacity-50"
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden />
          </button>
        </div>
      </div>

      <button onClick={runTest} disabled={testing} className="btn-gold mt-3 w-full !py-1.5 text-xs disabled:opacity-60">
        {testing ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> Test ediliyor…
          </>
        ) : (
          "Bağlantıyı Test Et"
        )}
      </button>

      {result && (
        <p className={`mt-2 flex items-start gap-1.5 text-xs ${result.ok ? "text-success" : "text-danger"}`}>
          {result.ok ? (
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          ) : (
            <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          )}
          {result.message}
        </p>
      )}
    </div>
  );
}
