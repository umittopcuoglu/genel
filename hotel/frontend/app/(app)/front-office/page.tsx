"use client";

import { PageHeader } from "@/components/ui/PageHeader";
import { useState } from "react";
import { ReservationTable } from "@/components/front-office/ReservationTable";
import { RoomBoard } from "@/components/front-office/RoomBoard";
import { TapeChart } from "@/components/front-office/TapeChart";
import { toast } from "@/components/ui/Toast";
import {
  MOCK_ARRIVALS,
  MOCK_DEPARTURES,
  MOCK_IN_HOUSE,
  MOCK_ROOMS,
  MOCK_TAPE_BLOCKS,
} from "@/lib/mock-frontoffice";
import type { ReservationRow } from "@/lib/types";

type Tab = "arrivals" | "departures" | "in-house" | "rooms" | "tape-chart";

const TABS: { id: Tab; label: string; count?: number }[] = [
  { id: "arrivals", label: "Gelenler", count: MOCK_ARRIVALS.length },
  { id: "departures", label: "Gidenler", count: MOCK_DEPARTURES.length },
  { id: "in-house", label: "Konaklayanlar", count: MOCK_IN_HOUSE.length },
  { id: "rooms", label: "Oda Panosu" },
  { id: "tape-chart", label: "Tape Chart" },
];

/**
 * Ön Büro ana ekranı — docs/03 §4.
 * Şimdilik mock veri; TASK-002 backend'i KABUL olunca lib/api.ts üzerinden
 * GET /api/v1/arrivals|departures|in-house|rooms endpoint'lerine bağlanır.
 */
export default function FrontOfficePage() {
  const [tab, setTab] = useState<Tab>("arrivals");
  const today = new Date().toLocaleDateString("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    weekday: "long",
  });

  async function handleCheckIn(row: ReservationRow) {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const response = await fetch(`/api/v1/checkin/${row.code}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token && { Authorization: `Bearer ${token}` }) },
      });
      if (!response.ok) throw new Error("Check-in başarısız");
      toast.success(`Check-in tamamlandı: ${row.code}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Check-in sırasında hata oluştu");
    }
  }

  async function handleCheckOut(row: ReservationRow) {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const response = await fetch(`/api/v1/checkout/${row.code}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token && { Authorization: `Bearer ${token}` }) },
      });
      if (!response.ok) throw new Error("Check-out başarısız");
      toast.success(`Check-out tamamlandı: ${row.code}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Check-out sırasında hata oluştu");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Ön Büro" subtitle={today} />

      <div className="border-b border-line" role="tablist" aria-label="Ön büro görünümleri">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`relative rounded-t-md px-4 py-2 text-sm font-medium transition ${
                tab === t.id
                  ? "border-b-2 border-primary text-primary"
                  : "text-text-2 hover:text-text-1"
              }`}
            >
              {t.label}
              {typeof t.count === "number" && (
                <span className="ml-1.5 rounded-full bg-bg px-1.5 py-0.5 text-xs">{t.count}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {tab === "arrivals" && (
        <ReservationTable
          rows={MOCK_ARRIVALS}
          emptyMessage="Bugün beklenen giriş yok."
          action={{
            label: "Check-in",
            onClick: handleCheckIn,
            enabled: (r) => r.status === "confirmed",
          }}
        />
      )}

      {tab === "departures" && (
        <ReservationTable
          rows={MOCK_DEPARTURES}
          emptyMessage="Bugün beklenen çıkış yok."
          action={{
            label: "Check-out",
            onClick: handleCheckOut,
            enabled: (r) => r.status === "checked_in",
          }}
        />
      )}

      {tab === "in-house" && (
        <ReservationTable rows={MOCK_IN_HOUSE} emptyMessage="Şu an konaklayan misafir yok." />
      )}

      {tab === "rooms" && <RoomBoard rooms={MOCK_ROOMS} />}

      {tab === "tape-chart" && (
        <TapeChart
          rooms={["101", "102", "103", "104", "105", "201", "202", "203", "204", "205", "301", "302", "303"]}
          blocks={MOCK_TAPE_BLOCKS}
        />
      )}
    </div>
  );
}
