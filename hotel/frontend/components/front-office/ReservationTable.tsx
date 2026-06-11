"use client";

import type { ReservationRow } from "@/lib/types";
import { ReservationStatusBadge } from "./StatusBadge";

interface Props {
  rows: ReservationRow[];
  emptyMessage: string;
  /** Satır eylemi: arrivals'ta "Check-in", departures'ta "Check-out" */
  action?: { label: string; onClick: (row: ReservationRow) => void; enabled?: (row: ReservationRow) => boolean };
}

/** Arrivals / Departures / In-House ortak liste tablosu — docs/03 §4 */
export function ReservationTable({ rows, emptyMessage, action }: Props) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-text-2">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
            <th className="px-4 py-3 font-medium">Rez. Kodu</th>
            <th className="px-4 py-3 font-medium">Misafir</th>
            <th className="px-4 py-3 font-medium">Oda Tipi</th>
            <th className="px-4 py-3 font-medium">Oda</th>
            <th className="px-4 py-3 font-medium">Giriş → Çıkış</th>
            <th className="px-4 py-3 font-medium">Kişi</th>
            <th className="px-4 py-3 font-medium">Durum</th>
            <th className="px-4 py-3 font-medium">Notlar</th>
            {action && <th className="px-4 py-3" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.reservation_id} className="border-b border-line last:border-0 hover:bg-bg/60">
              <td className="px-4 py-3 font-mono text-xs">{r.code}</td>
              <td className="px-4 py-3">
                <div className="font-medium">
                  {r.guest.first_name} {r.guest.last_name}
                </div>
                {r.guest.nationality && (
                  <div className="text-xs text-text-2">{r.guest.nationality}</div>
                )}
              </td>
              <td className="px-4 py-3">{r.room_type.name}</td>
              <td className="px-4 py-3 font-mono">{r.room_no ?? <span className="text-text-2">—</span>}</td>
              <td className="px-4 py-3 whitespace-nowrap">
                {r.check_in} → {r.check_out}
              </td>
              <td className="px-4 py-3">
                {r.adults}{r.kids > 0 ? ` + ${r.kids}ç` : ""}
              </td>
              <td className="px-4 py-3">
                <ReservationStatusBadge status={r.status} />
              </td>
              <td className="max-w-[200px] truncate px-4 py-3 text-text-2" title={r.special_requests ?? ""}>
                {r.special_requests ?? "—"}
              </td>
              {action && (
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => action.onClick(r)}
                    disabled={action.enabled ? !action.enabled(r) : false}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {action.label}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
