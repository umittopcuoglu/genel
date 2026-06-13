"use client";

import { useMemo, useState } from "react";
import { Plus, Search } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { MOCK_RESERVATIONS, type ReservationListItem } from "@/lib/mock-modules";
import { ReservationCreateModal } from "@/components/ReservationCreateModal";

const STATUS_TONE: Record<ReservationListItem["status"], { tone: BadgeTone; label: string }> = {
  confirmed: { tone: "info", label: "Onaylı" },
  checked_in: { tone: "success", label: "Konaklıyor" },
  checked_out: { tone: "neutral", label: "Ayrıldı" },
  cancelled: { tone: "danger", label: "İptal" },
  no_show: { tone: "warning", label: "Gelmedi" },
};

const SOURCE_LABEL: Record<ReservationListItem["source"], string> = {
  direct: "Direkt",
  ota: "OTA",
  walkin: "Walk-in",
  phone: "Telefon",
  corporate: "Kurumsal",
};

const FILTERS: { value: ReservationListItem["status"] | "all"; label: string }[] = [
  { value: "all", label: "Tümü" },
  { value: "confirmed", label: "Onaylı" },
  { value: "checked_in", label: "Konaklıyor" },
  { value: "checked_out", label: "Ayrıldı" },
  { value: "cancelled", label: "İptal" },
];

const fmtTRY = (n: number) => `₺${n.toLocaleString("tr-TR")}`;

/**
 * Rezervasyon Listesi — docs/03 §4. Filtre + arama + yeni rezervasyon.
 * Backend: GET /api/v1/reservations (TASK-003) bağlanınca mock kalkar.
 */
export default function ReservationsPage() {
  const [status, setStatus] = useState<ReservationListItem["status"] | "all">("all");
  const [q, setQ] = useState("");
  const [modalOpen, setModalOpen] = useState(false);

  const rows = useMemo(() => {
    return MOCK_RESERVATIONS.filter((r) => {
      const matchStatus = status === "all" || r.status === status;
      const matchQ =
        q === "" ||
        r.guest_name.toLowerCase().includes(q.toLowerCase()) ||
        r.code.toLowerCase().includes(q.toLowerCase());
      return matchStatus && matchQ;
    });
  }, [status, q]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rezervasyonlar"
        subtitle={`${MOCK_RESERVATIONS.length} kayıt`}
        action={
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            <Plus className="h-4 w-4" aria-hidden /> Yeni Rezervasyon
          </button>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Durum filtresi">
          {FILTERS.map((f) => (
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
              {f.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-2" aria-hidden />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Misafir veya kod ara…"
            aria-label="Rezervasyon ara"
            className="w-64 rounded-md border border-line bg-surface py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
              <th className="px-4 py-3 font-medium">Kod</th>
              <th className="px-4 py-3 font-medium">Misafir</th>
              <th className="px-4 py-3 font-medium">Oda Tipi</th>
              <th className="px-4 py-3 font-medium">Giriş → Çıkış</th>
              <th className="px-4 py-3 font-medium">Gece</th>
              <th className="px-4 py-3 font-medium">Kaynak</th>
              <th className="px-4 py-3 font-medium">Durum</th>
              <th className="px-4 py-3 text-right font-medium">Tutar</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const s = STATUS_TONE[r.status];
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
                  <td className="px-4 py-3 text-text-2">{SOURCE_LABEL[r.source]}</td>
                  <td className="px-4 py-3"><Badge tone={s.tone}>{s.label}</Badge></td>
                  <td className="px-4 py-3 text-right font-mono">{fmtTRY(r.total)}</td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-sm text-text-2">
                  Bu filtreye uyan rezervasyon yok.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <ReservationCreateModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={() => {
          // Liste yenileme - gerçek API'de window.location.reload() yerine SWR/React Query kullanılır
          window.location.reload();
        }}
      />
    </div>
  );
}
