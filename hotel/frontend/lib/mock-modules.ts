/**
 * Faz 5 modül ekranları için mock veri — backend (TASK-003…020) canlı bağlanana
 * kadar ekranları besler. Backend hazır olunca lib/api.ts üzerinden gerçek
 * endpoint'lere geçilir; bu dosya fallback olarak kalır.
 */

const TODAY = new Date().toISOString().slice(0, 10);
function addDays(base: string, days: number): string {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

/* ----------------------------- Rezervasyon ----------------------------- */
export interface ReservationListItem {
  id: string;
  code: string;
  guest_name: string;
  nationality: string;
  room_type: string;
  check_in: string;
  check_out: string;
  nights: number;
  source: "direct" | "ota" | "walkin" | "phone" | "corporate";
  status: "confirmed" | "checked_in" | "checked_out" | "cancelled" | "no_show";
  total: number;
}

export const MOCK_RESERVATIONS: ReservationListItem[] = [
  { id: "r-001", code: "RES-20260612-001", guest_name: "Ayşe Yılmaz", nationality: "TUR", room_type: "Deluxe", check_in: TODAY, check_out: addDays(TODAY, 3), nights: 3, source: "direct", status: "confirmed", total: 7350 },
  { id: "r-002", code: "RES-20260612-002", guest_name: "Hans Müller", nationality: "DEU", room_type: "Standart", check_in: TODAY, check_out: addDays(TODAY, 2), nights: 2, source: "ota", status: "checked_in", total: 4800 },
  { id: "r-003", code: "RES-20260612-003", guest_name: "Mehmet Demir", nationality: "TUR", room_type: "Junior Suite", check_in: TODAY, check_out: addDays(TODAY, 5), nights: 5, source: "corporate", status: "confirmed", total: 22500 },
  { id: "r-010", code: "RES-20260609-007", guest_name: "Elif Kaya", nationality: "TUR", room_type: "Deluxe", check_in: addDays(TODAY, -3), check_out: TODAY, nights: 3, source: "phone", status: "checked_in", total: 9600 },
  { id: "r-011", code: "RES-20260608-012", guest_name: "John Smith", nationality: "GBR", room_type: "Standart", check_in: addDays(TODAY, -4), check_out: TODAY, nights: 4, source: "ota", status: "checked_in", total: 9600 },
  { id: "r-020", code: "RES-20260610-004", guest_name: "Olga Petrova", nationality: "RUS", room_type: "Junior Suite", check_in: addDays(TODAY, -1), check_out: addDays(TODAY, 4), nights: 5, source: "ota", status: "checked_in", total: 22500 },
  { id: "r-030", code: "RES-20260605-018", guest_name: "Luca Rossi", nationality: "ITA", room_type: "Deluxe", check_in: addDays(TODAY, -7), check_out: addDays(TODAY, -2), nights: 5, source: "direct", status: "checked_out", total: 16000 },
  { id: "r-031", code: "RES-20260611-009", guest_name: "Sara Connor", nationality: "USA", room_type: "Standart", check_in: addDays(TODAY, 2), check_out: addDays(TODAY, 6), nights: 4, source: "walkin", status: "cancelled", total: 0 },
];

/* ----------------------------- Housekeeping ----------------------------- */
export interface HousekeepingTask {
  id: string;
  room_no: string;
  type: "checkout_clean" | "stayover" | "deep_clean" | "inspection";
  assigned_to: string | null;
  status: "pending" | "in_progress" | "done" | "inspected";
  priority: "low" | "normal" | "high";
  note: string | null;
}

export const MOCK_HK_TASKS: HousekeepingTask[] = [
  { id: "hk-1", room_no: "101", type: "checkout_clean", assigned_to: "Fatma A.", status: "in_progress", priority: "high", note: "Geç check-out sonrası" },
  { id: "hk-2", room_no: "102", type: "stayover", assigned_to: "Fatma A.", status: "pending", priority: "normal", note: null },
  { id: "hk-3", room_no: "204", type: "checkout_clean", assigned_to: "Zeynep K.", status: "done", priority: "normal", note: null },
  { id: "hk-4", room_no: "305", type: "deep_clean", assigned_to: null, status: "pending", priority: "high", note: "3 aylık derin temizlik" },
  { id: "hk-5", room_no: "118", type: "inspection", assigned_to: "Şef G.", status: "inspected", priority: "normal", note: null },
  { id: "hk-6", room_no: "501", type: "stayover", assigned_to: "Zeynep K.", status: "in_progress", priority: "low", note: "DND kaldırıldı" },
  { id: "hk-7", room_no: "202", type: "checkout_clean", assigned_to: null, status: "pending", priority: "normal", note: null },
  { id: "hk-8", room_no: "303", type: "deep_clean", assigned_to: "Fatma A.", status: "done", priority: "normal", note: null },
];

/* ------------------------------- Finance ------------------------------- */
export interface FolioRow {
  id: string;
  guest_name: string;
  room_no: string;
  charges: number;
  payments: number;
  balance: number;
  status: "open" | "closed";
}

export const MOCK_FOLIOS: FolioRow[] = [
  { id: "f-1", guest_name: "Hans Müller", room_no: "204", charges: 4800, payments: 4800, balance: 0, status: "open" },
  { id: "f-2", guest_name: "Elif Kaya", room_no: "305", charges: 11200, payments: 9600, balance: 1600, status: "open" },
  { id: "f-3", guest_name: "John Smith", room_no: "118", charges: 10350, payments: 5000, balance: 5350, status: "open" },
  { id: "f-4", guest_name: "Olga Petrova", room_no: "501", charges: 18400, payments: 22500, balance: -4100, status: "open" },
  { id: "f-5", guest_name: "Luca Rossi", room_no: "—", charges: 16000, payments: 16000, balance: 0, status: "closed" },
];

export interface FolioLine {
  date: string;
  description: string;
  type: "room" | "fnb" | "minibar" | "spa" | "tax" | "payment";
  amount: number;
}

export const MOCK_FOLIO_DETAIL: FolioLine[] = [
  { date: addDays(TODAY, -3), description: "Konaklama — Deluxe", type: "room", amount: 3200 },
  { date: addDays(TODAY, -3), description: "Restoran — Akşam yemeği", type: "fnb", amount: 740 },
  { date: addDays(TODAY, -2), description: "Konaklama — Deluxe", type: "room", amount: 3200 },
  { date: addDays(TODAY, -2), description: "Minibar", type: "minibar", amount: 180 },
  { date: addDays(TODAY, -1), description: "Konaklama — Deluxe", type: "room", amount: 3200 },
  { date: addDays(TODAY, -1), description: "SPA — Masaj", type: "spa", amount: 680 },
  { date: addDays(TODAY, -1), description: "KDV %10", type: "tax", amount: 1120 },
  { date: addDays(TODAY, -1), description: "Ödeme — Kredi Kartı", type: "payment", amount: -9600 },
];

/* ----------------------------- Maintenance ----------------------------- */
export interface WorkOrderRow {
  id: string;
  room_no: string;
  category: string;
  priority: "low" | "normal" | "high" | "urgent";
  description: string;
  assigned_to: string | null;
  status: "open" | "assigned" | "in_progress" | "resolved" | "closed";
  opened_at: string;
}

export const MOCK_WORK_ORDERS: WorkOrderRow[] = [
  { id: "wo-1", room_no: "305", category: "Klima", priority: "urgent", description: "Klima soğutmuyor, OOO işaretlendi", assigned_to: "Ali T.", status: "in_progress", opened_at: TODAY },
  { id: "wo-2", room_no: "118", category: "Tesisat", priority: "high", description: "Banyo musluğu damlatıyor", assigned_to: "Ali T.", status: "assigned", opened_at: TODAY },
  { id: "wo-3", room_no: "202", category: "Elektrik", priority: "normal", description: "Gece lambası çalışmıyor", assigned_to: null, status: "open", opened_at: addDays(TODAY, -1) },
  { id: "wo-4", room_no: "401", category: "Mobilya", priority: "low", description: "Sandalye gevşek", assigned_to: "Veli D.", status: "resolved", opened_at: addDays(TODAY, -2) },
  { id: "wo-5", room_no: "Lobi", category: "Aydınlatma", priority: "normal", description: "Avize ampulleri yanmış", assigned_to: "Veli D.", status: "closed", opened_at: addDays(TODAY, -4) },
];

export interface AssetRow {
  id: string;
  name: string;
  category: string;
  location: string;
  warranty_end: string;
  status: "active" | "maintenance" | "retired";
}

export const MOCK_ASSETS: AssetRow[] = [
  { id: "a-1", name: "HVAC Ünitesi - Kat 3", category: "HVAC", location: "Teknik Oda 3", warranty_end: "2027-01-15", status: "active" },
  { id: "a-2", name: "Jeneratör 250kVA", category: "Elektrik", location: "Bodrum", warranty_end: "2026-08-01", status: "active" },
  { id: "a-3", name: "Çamaşır Makinesi #2", category: "Çamaşırhane", location: "Çamaşırhane", warranty_end: "2025-12-01", status: "maintenance" },
  { id: "a-4", name: "Asansör A", category: "Asansör", location: "Ana Hol", warranty_end: "2028-03-20", status: "active" },
];

/* ------------------------------ Analytics ------------------------------ */
export const MOCK_OCCUPANCY_TREND = [
  { label: "Pzt", value: 72, secondary: 65 },
  { label: "Sal", value: 78, secondary: 70 },
  { label: "Çar", value: 81, secondary: 74 },
  { label: "Per", value: 85, secondary: 77 },
  { label: "Cum", value: 91, secondary: 82 },
  { label: "Cmt", value: 95, secondary: 88 },
  { label: "Paz", value: 88, secondary: 80 },
];

export const MOCK_REVENUE_TREND = [
  { label: "Oca", value: 1850000 },
  { label: "Şub", value: 1720000 },
  { label: "Mar", value: 2100000 },
  { label: "Nis", value: 2450000 },
  { label: "May", value: 2890000 },
  { label: "Haz", value: 3200000 },
];

export const MOCK_SOURCE_MIX = [
  { label: "Direct", value: 38, tone: "primary" as const },
  { label: "OTA", value: 34, tone: "info" as const },
  { label: "Corporate", value: 16, tone: "success" as const },
  { label: "Walk-in", value: 7, tone: "warning" as const },
  { label: "Phone", value: 5, tone: "neutral" as const },
];

/* ------------------------------- Settings ------------------------------ */
export interface UserRow {
  id: string;
  name: string;
  email: string;
  role: string;
  active: boolean;
  last_login: string;
}

export const MOCK_USERS: UserRow[] = [
  { id: "u-1", name: "Ümit Topçuoğlu", email: "umit@hotelops.local", role: "superadmin", active: true, last_login: TODAY },
  { id: "u-2", name: "Selin Manager", email: "selin@hotelops.local", role: "manager", active: true, last_login: TODAY },
  { id: "u-3", name: "Deniz Resepsiyon", email: "deniz@hotelops.local", role: "frontdesk", active: true, last_login: addDays(TODAY, -1) },
  { id: "u-4", name: "Fatma Kat", email: "fatma@hotelops.local", role: "housekeeping", active: true, last_login: addDays(TODAY, -1) },
  { id: "u-5", name: "Ali Teknik", email: "ali@hotelops.local", role: "maintenance", active: true, last_login: addDays(TODAY, -2) },
  { id: "u-6", name: "Ayhan Muhasebe", email: "ayhan@hotelops.local", role: "accounting", active: false, last_login: addDays(TODAY, -30) },
];

export const ROLES = [
  { key: "superadmin", label: "Süper Admin", desc: "Tam yetki — tüm modüller + sistem ayarları" },
  { key: "manager", label: "Müdür", desc: "Operasyon + raporlar + AI panelleri" },
  { key: "frontdesk", label: "Ön Büro", desc: "Check-in/out, rezervasyon, folio, kart" },
  { key: "housekeeping", label: "Housekeeping", desc: "Oda durumu, görevler, kayıp eşya" },
  { key: "accounting", label: "Muhasebe", desc: "Folio, ödeme, e-Fatura, gece denetimi" },
  { key: "maintenance", label: "Bakım", desc: "İş emri, varlık, önleyici bakım" },
  { key: "fb", label: "F&B", desc: "POS, menü, adisyon, stok" },
  { key: "hr", label: "İK", desc: "Çalışan, vardiya, puantaj, izin" },
  { key: "guest", label: "Misafir", desc: "Kendi rezervasyon/folio/KVKK görünümü" },
];

export { TODAY, addDays };
