/**
 * Alan tipleri — backend sözleşmesi (orchestrator/tasks/TASK-002.md) ile birebir.
 * Backend teslim edilince bu tipler API yanıtlarını doğrudan karşılar.
 */

export type RoomStatus = "clean" | "dirty" | "inspected" | "out_of_order" | "occupied";

export type ReservationStatus =
  | "confirmed"
  | "checked_in"
  | "checked_out"
  | "cancelled"
  | "no_show";

export type ReservationSource = "direct" | "ota" | "walkin" | "phone" | "corporate";

export interface RoomType {
  id: string;
  code: string;
  name: string;
  base_rate: number;
  capacity: number;
}

export interface Room {
  id: string;
  room_no: string;
  room_type: RoomType;
  floor: number;
  status: RoomStatus;
  notes: string | null;
  current_guest: GuestSummary | null;
}

export interface GuestSummary {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  nationality?: string;
}

export interface ReservationRow {
  reservation_id: string;
  code: string;
  guest: GuestSummary;
  room_type: Pick<RoomType, "id" | "code" | "name">;
  room_no?: string | null;
  check_in: string; // YYYY-MM-DD
  check_out: string;
  adults: number;
  kids: number;
  status: ReservationStatus;
  special_requests: string | null;
}

export interface Trace {
  id: string;
  reservation_id: string;
  department: "housekeeping" | "maintenance" | "concierge" | "front_office" | "manager";
  message: string;
  resolved: boolean;
  due_date: string | null;
}
