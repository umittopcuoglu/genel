"use client";

import { useState } from "react";
import { CreditCard } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatCard } from "@/components/kpi/StatCard";
import { MOCK_FOLIOS, MOCK_FOLIO_DETAIL, type FolioRow, type FolioLine } from "@/lib/mock-modules";
import { CurrencyRates, CurrencyConverter } from "@/components/CurrencyRates";
import { toast } from "@/components/ui/Toast";
import { useTranslation } from "@/lib/i18n";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";

const fmtTRY = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

const LINE_TONE: Record<FolioLine["type"], string> = {
  room: "text-text-1",
  fnb: "text-text-1",
  minibar: "text-text-1",
  spa: "text-text-1",
  tax: "text-text-2",
  payment: "text-emerald-600 dark:text-emerald-400",
};

// Folio satırı + detay satırlarını taşıyan zenginleştirilmiş tip.
type FolioRowX = FolioRow & { lines?: FolioLine[] };

const LINE_TYPES = ["room", "fnb", "minibar", "spa", "tax"] as const;

/**
 * Backend FolioResponse (TASK-004; guest_name/room_no/items/payments ile zenginleştirilmiş)
 * → ekran satır şekline normalizasyon. Hem canlı hem mock şekliyle çalışır (?? guard'lı).
 */
function normalizeFolios(raw: any[]): FolioRowX[] {
  return raw.map((f) => {
    const charges = Number(f.total ?? f.charges ?? 0);
    const paymentsArr = Array.isArray(f.payments) ? f.payments : null;
    const payments = paymentsArr
      ? paymentsArr.reduce((s: number, p: any) => s + Number(p.amount ?? 0), 0)
      : Number(f.payments ?? 0);

    let lines: FolioLine[] | undefined;
    if (Array.isArray(f.items) || paymentsArr) {
      const itemLines: FolioLine[] = (f.items ?? []).map((it: any) => ({
        date: String(it.posted_at ?? it.created_at ?? "").slice(0, 10),
        description: it.description ?? "—",
        type: (LINE_TYPES as readonly string[]).includes(it.type) ? it.type : "fnb",
        amount: Number(it.total ?? 0),
      }));
      const payLines: FolioLine[] = (paymentsArr ?? []).map((p: any) => ({
        date: String(p.created_at ?? "").slice(0, 10),
        description: `Ödeme — ${p.method ?? ""}`.trim(),
        type: "payment" as const,
        amount: -Number(p.amount ?? 0),
      }));
      lines = [...itemLines, ...payLines];
    }

    return {
      id: String(f.id),
      guest_name: f.guest_name ?? "—",
      room_no: f.room_no ?? "—",
      charges,
      payments,
      balance: Number(f.balance ?? 0),
      status: String(f.status ?? "open").toLowerCase() === "closed" ? "closed" : "open",
      lines,
    };
  });
}

/**
 * Muhasebe & Cashiering — folio listesi + seçili folio detayı (docs/03 §4).
 * Backend: GET /api/v1/folios (TASK-004) — bağlantı yoksa mock fallback.
 */
export default function FinancePage() {
  const { t } = useTranslation();
  const { data: foliosRaw, usingFallback } = useApiData<any[]>({
    path: "/api/v1/folios",
    fallback: MOCK_FOLIOS,
    responseKey: "data",
  });
  const folios = normalizeFolios(foliosRaw ?? []);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected: FolioRowX | undefined =
    folios.find((f) => f.id === selectedId) ?? folios[Math.min(1, folios.length - 1)] ?? folios[0];
  const detailLines: FolioLine[] = selected?.lines ?? MOCK_FOLIO_DETAIL;

  const totalCharges = folios.reduce((s, f) => s + f.charges, 0);
  const totalPayments = folios.reduce((s, f) => s + f.payments, 0);
  const openBalance = folios.filter((f) => f.status === "open").reduce((s, f) => s + f.balance, 0);

  return (
    <div className="space-y-6">
      <PageHeader title={t("finance.title")} subtitle={t("finance.subtitle")} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t("finance.totalCharges")} value={fmtTRY(totalCharges)} />
        <StatCard label={t("finance.totalPayments")} value={fmtTRY(totalPayments)} tone="success" />
        <StatCard label={t("finance.openBalance")} value={fmtTRY(openBalance)} tone={openBalance > 0 ? "warning" : "default"} />
        <StatCard label={t("finance.openFolios")} value={String(folios.filter((f) => f.status === "open").length)} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Card title="Folio'lar">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-text-2">
                    <th className="px-2 py-2 font-medium">Misafir</th>
                    <th className="px-2 py-2 font-medium">Oda</th>
                    <th className="px-2 py-2 text-right font-medium">Masraf</th>
                    <th className="px-2 py-2 text-right font-medium">Ödeme</th>
                    <th className="px-2 py-2 text-right font-medium">Bakiye</th>
                    <th className="px-2 py-2 font-medium">Durum</th>
                  </tr>
                </thead>
                <tbody>
                  {folios.map((f) => (
                    <tr
                      key={f.id}
                      onClick={() => setSelectedId(f.id)}
                      className={`cursor-pointer border-b border-line last:border-0 hover:bg-bg/60 ${
                        selected?.id === f.id ? "bg-primary/5" : ""
                      }`}
                    >
                      <td className="px-2 py-2.5 font-medium">{f.guest_name}</td>
                      <td className="px-2 py-2.5 font-mono">{f.room_no}</td>
                      <td className="px-2 py-2.5 text-right font-mono">{fmtTRY(f.charges)}</td>
                      <td className="px-2 py-2.5 text-right font-mono">{fmtTRY(f.payments)}</td>
                      <td className={`px-2 py-2.5 text-right font-mono ${f.balance > 0 ? "text-danger" : f.balance < 0 ? "text-emerald-600" : ""}`}>
                        {fmtTRY(f.balance)}
                      </td>
                      <td className="px-2 py-2.5">
                        <Badge tone={f.status === "open" ? "info" : "neutral"}>{f.status === "open" ? "Açık" : "Kapalı"}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card
            title={`Folio — ${selected?.guest_name ?? "—"}`}
            action={
              <button
                onClick={() => toast.info("Ödeme alma formu yakında eklenecek")}
                className="flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-white hover:opacity-90"
              >
                <CreditCard className="h-3.5 w-3.5" aria-hidden /> {t("finance.takePayment")}
              </button>
            }
          >
            <div className="space-y-1.5">
              {detailLines.map((l, i) => (
                <div key={i} className="flex items-center justify-between border-b border-line py-1.5 text-xs last:border-0">
                  <div>
                    <div className={LINE_TONE[l.type]}>{l.description}</div>
                    <div className="text-text-2">{l.date}</div>
                  </div>
                  <span className={`font-mono ${l.amount < 0 ? "text-emerald-600 dark:text-emerald-400" : ""}`}>
                    {fmtTRY(l.amount)}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between pt-2 text-sm font-semibold">
                <span>{t("finance.balance")}</span>
                <span className={`font-mono ${(selected?.balance ?? 0) > 0 ? "text-danger" : ""}`}>{fmtTRY(selected?.balance ?? 0)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Döviz Kurları — Dış misafirler için */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title={t("finance.exchangeRates")}>
          <CurrencyRates baseCurrency="TRY" />
        </Card>
        <Card title={t("finance.currencyConverter")}>
          <CurrencyConverter />
        </Card>
      </div>
    </div>
  );
}
