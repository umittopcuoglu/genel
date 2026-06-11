/**
 * Ön Büro mock verisi — TASK-002 backend'i KABUL olana kadar ekranları besler.
 * Backend hazır olunca lib/api.ts üzerinden gerçek endpoint'lere bağlanır;
 * bu dosya yalnızca fallback olarak kalır.
 */
import type { ReservationRow, Room } from "./types";

const TODAY = new Date().toISOString().slice(0, 10);

function addDays(base: string, days: number): string {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export const MOCK_ARRIVALS: ReservationRow[] = [
  {
    reservation_id: "r-001",
    code: "RES-20260612-001",
    guest: { id: "g-1", first_name: "Ayşe", last_name: "Yılmaz", nationality: "TUR" },
    room_type: { id: "t-1", code: "DLX", name: "Deluxe" },
    room_no: null,
    check_in: TODAY,
    check_out: addDays(TODAY, 3),
    adults: 2,
    kids: 0,
    status: "confirmed",
    special_requests: "Yüksek kat, deniz manzarası",
  },
  {
    reservation_id: "r-002",
    code: "RES-20260612-002",
    guest: { id: "g-2", first_name: "Hans", last_name: "Müller", nationality: "DEU" },
    room_type: { id: "t-2", code: "STD", name: "Standart" },
    room_no: "204",
    check_in: TODAY,
    check_out: addDays(TODAY, 2),
    adults: 1,
    kids: 0,
    status: "checked_in",
    special_requests: null,
  },
  {
    reservation_id: "r-003",
    code: "RES-20260612-003",
    guest: { id: "g-3", first_name: "Mehmet", last_name: "Demir", nationality: "TUR" },
    room_type: { id: "t-3", code: "JNR", name: "Junior Suite" },
    room_no: null,
    check_in: TODAY,
    check_out: addDays(TODAY, 5),
    adults: 2,
    kids: 2,
    status: "confirmed",
    special_requests: "Bebek yatağı",
  },
];

export const MOCK_DEPARTURES: ReservationRow[] = [
  {
    reservation_id: "r-010",
    code: "RES-20260609-007",
    guest: { id: "g-10", first_name: "Elif", last_name: "Kaya", nationality: "TUR" },
    room_type: { id: "t-1", code: "DLX", name: "Deluxe" },
    room_no: "305",
    check_in: addDays(TODAY, -3),
    check_out: TODAY,
    adults: 2,
    kids: 1,
    status: "checked_in",
    special_requests: null,
  },
  {
    reservation_id: "r-011",
    code: "RES-20260608-012",
    guest: { id: "g-11", first_name: "John", last_name: "Smith", nationality: "GBR" },
    room_type: { id: "t-2", code: "STD", name: "Standart" },
    room_no: "118",
    check_in: addDays(TODAY, -4),
    check_out: TODAY,
    adults: 1,
    kids: 0,
    status: "checked_in",
    special_requests: "Geç check-out talebi (14:00)",
  },
];

export const MOCK_IN_HOUSE: ReservationRow[] = [
  ...MOCK_DEPARTURES,
  {
    reservation_id: "r-020",
    code: "RES-20260610-004",
    guest: { id: "g-20", first_name: "Olga", last_name: "Petrova", nationality: "RUS" },
    room_type: { id: "t-3", code: "JNR", name: "Junior Suite" },
    room_no: "501",
    check_in: addDays(TODAY, -1),
    check_out: addDays(TODAY, 4),
    adults: 2,
    kids: 0,
    status: "checked_in",
    special_requests: null,
  },
];

/** 3 kat × 10 oda örnek pano */
export const MOCK_ROOMS: Room[] = Array.from({ length: 30 }, (_, i) => {
  const floor = Math.floor(i / 10) + 1;
  const no = `${floor}${String((i % 10) + 1).padStart(2, "0")}`;
  const statuses = ["clean", "dirty", "inspected", "occupied", "clean", "clean", "dirty", "occupied", "inspected", "out_of_order"] as const;
  const status = statuses[i % statuses.length];
  return {
    id: `room-${no}`,
    room_no: no,
    room_type: {
      id: i % 3 === 0 ? "t-3" : i % 2 === 0 ? "t-1" : "t-2",
      code: i % 3 === 0 ? "JNR" : i % 2 === 0 ? "DLX" : "STD",
      name: i % 3 === 0 ? "Junior Suite" : i % 2 === 0 ? "Deluxe" : "Standart",
      base_rate: i % 3 === 0 ? 4500 : i % 2 === 0 ? 3200 : 2400,
      capacity: i % 3 === 0 ? 4 : 2,
    },
    floor,
    status,
    notes: status === "out_of_order" ? "Klima arızası — bakım bekleniyor" : null,
    current_guest:
      status === "occupied"
        ? { id: `g-${i}`, first_name: "Misafir", last_name: `#${no}` }
        : null,
  };
});

/** Tape Chart için: oda × gün doluluk blokları */
export interface TapeBlock {
  room_no: string;
  guest_name: string;
  start: string; // YYYY-MM-DD
  nights: number;
  status: "confirmed" | "checked_in";
}

export const MOCK_TAPE_BLOCKS: TapeBlock[] = [
  { room_no: "101", guest_name: "A. Yılmaz", start: TODAY, nights: 3, status: "confirmed" },
  { room_no: "102", guest_name: "H. Müller", start: addDays(TODAY, -1), nights: 3, status: "checked_in" },
  { room_no: "104", guest_name: "O. Petrova", start: addDays(TODAY, -1), nights: 5, status: "checked_in" },
  { room_no: "201", guest_name: "M. Demir", start: addDays(TODAY, 1), nights: 4, status: "confirmed" },
  { room_no: "203", guest_name: "E. Kaya", start: addDays(TODAY, -3), nights: 3, status: "checked_in" },
  { room_no: "205", guest_name: "J. Smith", start: addDays(TODAY, 2), nights: 2, status: "confirmed" },
  { room_no: "301", guest_name: "L. Rossi", start: addDays(TODAY, 4), nights: 7, status: "confirmed" },
  { room_no: "302", guest_name: "K. Tanaka", start: TODAY, nights: 2, status: "checked_in" },
];

export { TODAY, addDays };
