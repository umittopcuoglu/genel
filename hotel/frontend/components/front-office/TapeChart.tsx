"use client";

import { useMemo, useState } from "react";
import type { TapeBlock } from "@/lib/mock-frontoffice";

interface Props {
  rooms: string[]; // oda numaraları (satırlar)
  blocks: TapeBlock[]; // rezervasyon blokları
  days?: number; // görünüm genişliği (varsayılan 14 gün)
}

function fmt(d: Date): string {
  return d.toISOString().slice(0, 10);
}

const DAY_LABELS = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];

/**
 * Tape Chart — 14 günlük oda × tarih ızgarası (docs/03 §4).
 * Faz 1: görüntüleme + hover detay. Drag-drop oda değişimi backend
 * TASK-002 KABUL olunca eklenecek (PATCH /room-assign).
 */
export function TapeChart({ rooms, blocks, days = 14 }: Props) {
  const [offset, setOffset] = useState(0); // gün kaydırma

  const dates = useMemo(() => {
    const start = new Date();
    start.setDate(start.getDate() + offset);
    return Array.from({ length: days }, (_, i) => {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      return d;
    });
  }, [offset, days]);

  const dateStrs = dates.map(fmt);
  const todayStr = fmt(new Date());

  // oda → { dateStr → block } haritası
  const cellMap = useMemo(() => {
    const map = new Map<string, Map<string, { block: TapeBlock; isStart: boolean }>>();
    for (const b of blocks) {
      const roomMap = map.get(b.room_no) ?? new Map();
      const start = new Date(b.start);
      for (let n = 0; n < b.nights; n++) {
        const d = new Date(start);
        d.setDate(d.getDate() + n);
        roomMap.set(fmt(d), { block: b, isStart: n === 0 });
      }
      map.set(b.room_no, roomMap);
    }
    return map;
  }, [blocks]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setOffset((o) => o - 7)}
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-bg"
            aria-label="7 gün geri"
          >
            ← 7 gün
          </button>
          <button
            onClick={() => setOffset(0)}
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-bg"
          >
            Bugün
          </button>
          <button
            onClick={() => setOffset((o) => o + 7)}
            className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-bg"
            aria-label="7 gün ileri"
          >
            7 gün →
          </button>
        </div>
        <div className="flex items-center gap-4 text-xs text-text-2">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-emerald-500" /> Konaklıyor
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-sky-500" /> Onaylı
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-bg">
              <th className="sticky left-0 z-10 border-b border-r border-line bg-bg px-3 py-2 text-left font-medium">
                Oda
              </th>
              {dates.map((d) => {
                const ds = fmt(d);
                const isToday = ds === todayStr;
                const isWeekend = d.getDay() === 0 || d.getDay() === 6;
                return (
                  <th
                    key={ds}
                    className={`min-w-[64px] border-b border-line px-1 py-2 text-center font-medium ${
                      isToday ? "bg-primary/10 text-primary" : isWeekend ? "bg-bg/80 text-text-2" : "text-text-2"
                    }`}
                  >
                    <div>{DAY_LABELS[d.getDay()]}</div>
                    <div className="font-semibold">{d.getDate()}</div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {rooms.map((roomNo) => {
              const roomCells = cellMap.get(roomNo);
              return (
                <tr key={roomNo} className="border-b border-line last:border-0">
                  <td className="sticky left-0 z-10 border-r border-line bg-surface px-3 py-1.5 font-mono font-semibold">
                    {roomNo}
                  </td>
                  {dateStrs.map((ds) => {
                    const cell = roomCells?.get(ds);
                    if (!cell) {
                      return <td key={ds} className={ds === todayStr ? "bg-primary/5" : ""} />;
                    }
                    const color =
                      cell.block.status === "checked_in" ? "bg-emerald-500" : "bg-sky-500";
                    return (
                      <td key={ds} className="p-0.5">
                        <div
                          className={`h-6 ${color} ${cell.isStart ? "rounded-l-md pl-1.5" : ""} flex items-center overflow-hidden whitespace-nowrap text-[10px] font-medium text-white`}
                          title={`${cell.block.guest_name} · ${cell.block.start} +${cell.block.nights} gece`}
                        >
                          {cell.isStart ? cell.block.guest_name : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
