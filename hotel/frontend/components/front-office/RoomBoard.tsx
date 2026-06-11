"use client";

import { useMemo, useState } from "react";
import type { Room, RoomStatus } from "@/lib/types";
import { RoomStatusBadge } from "./StatusBadge";

const FILTERS: { value: RoomStatus | "all"; label: string }[] = [
  { value: "all", label: "Tümü" },
  { value: "clean", label: "Temiz" },
  { value: "inspected", label: "Kontrol Edildi" },
  { value: "dirty", label: "Kirli" },
  { value: "occupied", label: "Dolu" },
  { value: "out_of_order", label: "Arızalı" },
];

const STATUS_BORDER: Record<RoomStatus, string> = {
  clean: "border-l-emerald-500",
  inspected: "border-l-sky-500",
  dirty: "border-l-amber-500",
  occupied: "border-l-indigo-500",
  out_of_order: "border-l-red-500",
};

/** Oda durum panosu — kat bazında gruplu kart ızgarası (docs/03 §4) */
export function RoomBoard({ rooms }: { rooms: Room[] }) {
  const [filter, setFilter] = useState<RoomStatus | "all">("all");

  const byFloor = useMemo(() => {
    const filtered = filter === "all" ? rooms : rooms.filter((r) => r.status === filter);
    const groups = new Map<number, Room[]>();
    for (const room of filtered) {
      const list = groups.get(room.floor) ?? [];
      list.push(room);
      groups.set(room.floor, list);
    }
    return Array.from(groups.entries()).sort(([a], [b]) => a - b);
  }, [rooms, filter]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Oda durumu filtresi">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            aria-pressed={filter === f.value}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
              filter === f.value
                ? "border-primary bg-primary text-white"
                : "border-line bg-surface text-text-2 hover:text-text-1"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {byFloor.length === 0 && (
        <div className="rounded-lg border border-dashed border-line p-10 text-center text-sm text-text-2">
          Bu filtreye uyan oda yok.
        </div>
      )}

      {byFloor.map(([floor, floorRooms]) => (
        <section key={floor} aria-label={`Kat ${floor}`}>
          <h3 className="mb-2 text-sm font-semibold text-text-2">Kat {floor}</h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {floorRooms.map((room) => (
              <div
                key={room.id}
                className={`rounded-lg border border-line border-l-4 bg-surface p-3 ${STATUS_BORDER[room.status]}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-lg font-semibold">{room.room_no}</span>
                  <span className="text-xs text-text-2">{room.room_type.code}</span>
                </div>
                <div className="mt-2">
                  <RoomStatusBadge status={room.status} />
                </div>
                {room.current_guest && (
                  <div className="mt-2 truncate text-xs text-text-2">
                    {room.current_guest.first_name} {room.current_guest.last_name}
                  </div>
                )}
                {room.notes && (
                  <div className="mt-1 truncate text-xs text-red-600 dark:text-red-400" title={room.notes}>
                    ⚠ {room.notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
