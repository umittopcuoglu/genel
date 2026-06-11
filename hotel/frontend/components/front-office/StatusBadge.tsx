import type { ReservationStatus, RoomStatus } from "@/lib/types";

const ROOM_STYLES: Record<RoomStatus, { label: string; cls: string }> = {
  clean: { label: "Temiz", cls: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300" },
  inspected: { label: "Kontrol Edildi", cls: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300" },
  dirty: { label: "Kirli", cls: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300" },
  occupied: { label: "Dolu", cls: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300" },
  out_of_order: { label: "Arızalı", cls: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300" },
};

const RES_STYLES: Record<ReservationStatus, { label: string; cls: string }> = {
  confirmed: { label: "Onaylı", cls: "bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300" },
  checked_in: { label: "Konaklıyor", cls: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300" },
  checked_out: { label: "Ayrıldı", cls: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300" },
  cancelled: { label: "İptal", cls: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300" },
  no_show: { label: "Gelmedi", cls: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300" },
};

export function RoomStatusBadge({ status }: { status: RoomStatus }) {
  const s = ROOM_STYLES[status];
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}

export function ReservationStatusBadge({ status }: { status: ReservationStatus }) {
  const s = RES_STYLES[status];
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  );
}
