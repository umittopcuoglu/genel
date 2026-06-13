"use client";

import { useMemo, useState, useEffect } from "react";
import { Plus, Search, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { MOCK_RESERVATIONS, type ReservationListItem } from "@/lib/mock-modules";
import { ReservationCreateModal } from "@/components/ReservationCreateModal";
import { api, ApiRequestError } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

const STATUS_TONES: Record<ReservationListItem["status"], BadgeTone> = {
  confirmed: "info",
  checked_in: "success",
  checked_out: "neutral",
  cancelled: "danger",
  no_show: "warning",
};

const FILTER_KEYS: { value: ReservationListItem["status"] | "all"; labelKey: string }[] = [
  { value: "all", labelKey: "common.all" },
  { value: "confirmed", labelKey: "reservations.status.confirmed" },
  { value: "checked_in", labelKey: "reservations.status.checkedIn" },
  { value: "checked_out", labelKey: "reservations.status.checkedOut" },
  { value: "cancelled", labelKey: "reservations.status.cancelled" },
];

const fmtTRY = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

/**
 * Rezervasyon Listesi — docs/03 §4. Filtre + arama + yeni rezervasyon.
 * Backend: GET /api/v1/reservations (TASK-003) bağlanınca mock kalkar.
 */
export default function ReservationsPage() {
  const { t, language } = useTranslation();
  const [status, setStatus] = useState<ReservationListItem["status"] | "all">("all");
  const [q, setQ] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [data, setData] = useState<ReservationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMock, setUsingMock] = useState(false);

  const fetchReservations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api<{ data: ReservationListItem[]; meta?: any }>("/api/v1/reservations");
      setData(Array.isArray(response.data) ? response.data : []);
      setUsingMock(false);
    } catch (err) {
      // API başarısız → mock veriye düş, kullanıcıya bildir
      console.warn("API yanıt vermedi, mock veri gösteriliyor:", err);
      setData(MOCK_RESERVATIONS);
      setUsingMock(true);
      if (err instanceof ApiRequestError && err.status !== 0) {
        setError(`API hatası (${err.status})`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReservations();
  }, []);

  const rows = useMemo(() => {
    return data.filter((r) => {
      const matchStatus = status === "all" || r.status === status;
      const matchQ =
        q === "" ||
        r.guest_name.toLowerCase().includes(q.toLowerCase()) ||
        r.code.toLowerCase().includes(q.toLowerCase());
      return matchStatus && matchQ;
    });
  }, [status, q, data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("reservations.title")}
        subtitle={`${data.length} ${language === "tr" ? "kayıt" : "records"}${usingMock ? (language === "tr" ? " (mock veri)" : " (mock data)") : ""}`}
        action={
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            <Plus className="h-4 w-4" aria-hidden /> {t("reservations.newReservation")}
          </button>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2" role="group" aria-label={t("common.filter")}>
          {FILTER_KEYS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatus(f.value)}
              aria-pressed={status === f.value}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                status === f.value
                  ? "border-primary bg-primary text-white"
                  : "border-line bg-surface text-text-2 hover:text-text-1"
              }`}
            >
              {t(f.labelKey)}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-2" aria-hidden />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("reservations.searchPlaceholder")}
            aria-label={t("common.search")}
            className="w-64 rounded-md border border-line bg-surface py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 p-3 text-sm text-amber-800 dark:text-amber-200">
          ⚠️ {error} — Mock veri gösteriliyor
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
          <span className="ml-3 text-text-2">{t("reservations.loading")}</span>
        </div>
      ) : (
      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
              <th className="px-4 py-3 font-medium">{t("reservations.code")}</th>
              <th className="px-4 py-3 font-medium">{t("reservations.guestName")}</th>
              <th className="px-4 py-3 font-medium">{t("reservations.roomType")}</th>
              <th className="px-4 py-3 font-medium">{t("reservations.checkInDate")} → {t("reservations.checkOutDate")}</th>
              <th className="px-4 py-3 font-medium">{t("reservations.nights")}</th>
              <th className="px-4 py-3 font-medium">{t("reservations.source")}</th>
              <th className="px-4 py-3 font-medium">{t("common.status")}</th>
              <th className="px-4 py-3 text-right font-medium">{t("reservations.amount")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const statusKey = r.status === "checked_in" ? "checkedIn" :
                                r.status === "checked_out" ? "checkedOut" :
                                r.status === "no_show" ? "noShow" : r.status;
              return (
                <tr key={r.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                  <td className="px-4 py-3 font-mono text-xs">{r.code}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{r.guest_name}</div>
                    <div className="text-xs text-text-2">{r.nationality}</div>
                  </td>
                  <td className="px-4 py-3">{r.room_type}</td>
                  <td className="whitespace-nowrap px-4 py-3">{r.check_in} → {r.check_out}</td>
                  <td className="px-4 py-3">{r.nights}</td>
                  <td className="px-4 py-3 text-text-2">{t(`reservations.source.${r.source}`)}</td>
                  <td className="px-4 py-3"><Badge tone={STATUS_TONES[r.status]}>{t(`reservations.status.${statusKey}`)}</Badge></td>
                  <td className="px-4 py-3 text-right font-mono">{fmtTRY(r.total)}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-sm text-text-2">
                  {t("reservations.noResults")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      )}

      <ReservationCreateModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => {
          fetchReservations();
        }}
      />
    </div>
  );
}
