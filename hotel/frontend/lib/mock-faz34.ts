/**
 * Faz 3-4 modül ekranları için mock veri (Groups, F&B, Security/KVKK, HR, GDS, IoT,
 * CV, Voice, Multi-Property, Mobile, Blockchain). Backend hazır (201 test yeşil);
 * gerçek bağlantı lib/api.ts üzerinden yapılınca bu dosya fallback kalır.
 */

const TODAY = new Date().toISOString().slice(0, 10);
const addDays = (b: string, d: number) => {
  const x = new Date(b);
  x.setDate(x.getDate() + d);
  return x.toISOString().slice(0, 10);
};

/* ───────── Groups & Events ───────── */
export const MOCK_GROUPS = [
  { id: "g1", name: "Touresco Konferans 2026", status: "confirmed", start: "2026-07-01", end: "2026-07-05", pax: 50, discount: 10, blocks: 45 },
  { id: "g2", name: "Acme Düğün", status: "inquiry", start: "2026-08-12", end: "2026-08-14", pax: 120, discount: 15, blocks: 0 },
  { id: "g3", name: "MedTech Fuarı", status: "confirmed", start: "2026-09-20", end: "2026-09-23", pax: 80, discount: 12, blocks: 72 },
  { id: "g4", name: "Yıldız Holding Toplantısı", status: "completed", start: "2026-05-10", end: "2026-05-11", pax: 30, discount: 8, blocks: 30 },
];
export const MOCK_EVENTS = [
  { id: "e1", title: "Açılış Galası", group: "Touresco Konferans 2026", venue: "Balo Salonu", capacity: 200, setup: "banquet", date: "2026-07-01 19:00", catering: true },
  { id: "e2", title: "Genel Kurul", group: "MedTech Fuarı", venue: "Salon A", capacity: 80, setup: "theatre", date: "2026-09-20 09:00", catering: false },
  { id: "e3", title: "Networking Kokteyli", group: "Touresco Konferans 2026", venue: "Teras", capacity: 150, setup: "cocktail", date: "2026-07-02 18:00", catering: true },
];

/* ───────── F&B / POS ───────── */
export const MOCK_OUTLETS = [
  { id: "o1", name: "Ana Restoran", type: "restaurant", open: true, todaySales: 48500 },
  { id: "o2", name: "Lobi Bar", type: "bar", open: true, todaySales: 12300 },
  { id: "o3", name: "Havuz Bar", type: "bar", open: true, todaySales: 8700 },
  { id: "o4", name: "Room Service", type: "room_service", open: true, todaySales: 6400 },
];
export const MOCK_CHECKS = [
  { id: "c1", outlet: "Ana Restoran", table: "12", room: "204", items: 5, total: 1240, status: "open" },
  { id: "c2", outlet: "Lobi Bar", table: "—", room: "305", items: 3, total: 480, status: "open" },
  { id: "c3", outlet: "Ana Restoran", table: "7", room: null, items: 8, total: 2150, status: "closed" },
  { id: "c4", outlet: "Room Service", table: "—", room: "501", items: 2, total: 320, status: "open" },
];
export const MOCK_MENU = [
  { id: "m1", name: "Izgara Levrek", category: "Ana Yemek", price: 480, cost: 180, popular: true },
  { id: "m2", name: "Sezar Salata", category: "Başlangıç", price: 240, cost: 70, popular: true },
  { id: "m3", name: "Tiramisu", category: "Tatlı", price: 180, cost: 45, popular: false },
  { id: "m4", name: "Ev Şarabı (kadeh)", category: "İçecek", price: 220, cost: 60, popular: true },
];

/* ───────── Security / KVKK ───────── */
export const MOCK_ACCESS_LOGS = [
  { id: "a1", area: "Oda 204", card: "KC-0204", who: "Hans Müller (misafir)", time: `${TODAY} 14:32`, result: "granted" },
  { id: "a2", area: "Personel Girişi", card: "KC-STAFF-12", who: "Ali Teknik", time: `${TODAY} 08:01`, result: "granted" },
  { id: "a3", area: "Oda 305", card: "KC-0305", who: "Bilinmeyen", time: `${TODAY} 03:14`, result: "denied" },
  { id: "a4", area: "Kasa Odası", card: "KC-STAFF-03", who: "Ayhan Muhasebe", time: `${TODAY} 11:20`, result: "granted" },
];
export const MOCK_KEYCARDS = [
  { id: "k1", code: "KC-0204", owner: "Hans Müller", type: "guest", valid: "2026-06-12 → 2026-06-14", status: "active" },
  { id: "k2", code: "KC-0305", owner: "Elif Kaya", type: "guest", valid: "2026-06-09 → 2026-06-12", status: "expired" },
  { id: "k3", code: "KC-STAFF-12", owner: "Ali Teknik", type: "staff", valid: "süresiz", status: "active" },
];
export const MOCK_KVKK = [
  { id: "kv1", guest: "Hans Müller", purpose: "Pazarlama izni", date: "2026-06-12", status: "granted" },
  { id: "kv2", guest: "Elif Kaya", purpose: "Veri silme talebi", date: "2026-06-11", status: "pending" },
  { id: "kv3", guest: "John Smith", purpose: "Veri erişim talebi", date: "2026-06-10", status: "completed" },
];

/* ───────── HR / Shift ───────── */
export const MOCK_EMPLOYEES = [
  { id: "emp1", code: "EMP001", name: "Ahmet Yılmaz", dept: "Ön Büro", position: "Resepsiyonist", leave: 12 },
  { id: "emp2", code: "EMP002", name: "Ayşe Demir", dept: "Housekeeping", position: "Kat Görevlisi", leave: 8 },
  { id: "emp3", code: "EMP003", name: "Ali Teknik", dept: "Bakım", position: "Teknisyen", leave: 15 },
  { id: "emp4", code: "EMP004", name: "Zeynep Kaya", dept: "Housekeeping", position: "Kat Şefi", leave: 18 },
];
export const MOCK_SHIFTS = [
  { id: "s1", name: "Sabah", dept: "Ön Büro", time: "07:00–15:00", min: 2, max: 4, assigned: 3 },
  { id: "s2", name: "Akşam", dept: "Ön Büro", time: "15:00–23:00", min: 2, max: 3, assigned: 2 },
  { id: "s3", name: "Gece", dept: "Ön Büro", time: "23:00–07:00", min: 1, max: 2, assigned: 1 },
];
export const MOCK_LEAVES = [
  { id: "l1", emp: "Ahmet Yılmaz", type: "Yıllık", range: "2026-07-01 → 2026-07-07", days: 5, status: "pending" },
  { id: "l2", emp: "Ayşe Demir", type: "Hastalık", range: "2026-06-13 → 2026-06-14", days: 2, status: "approved" },
  { id: "l3", emp: "Ali Teknik", type: "Mazeret", range: "2026-06-20", days: 1, status: "rejected" },
];

/* ───────── GDS ───────── */
export const MOCK_GDS_CHANNELS = [
  { id: "gd1", code: "AMADEUS", name: "Amadeus", provider: "amadeus", active: true, actions: "ARI push + Rez pull" },
  { id: "gd2", code: "SABRE", name: "Sabre", provider: "sabre", active: true, actions: "ARI push" },
  { id: "gd3", code: "TRVL", name: "Travelport", provider: "travelport", active: false, actions: "—" },
];
export const MOCK_GDS_RES = [
  { id: "gr1", gdsId: "AMAD-99213", guest: "Pierre Dubois", channel: "Amadeus", checkin: addDays(TODAY, 5), nights: 3, status: "synced", total: 9600 },
  { id: "gr2", gdsId: "SABR-44120", guest: "Maria Garcia", channel: "Sabre", checkin: addDays(TODAY, 8), nights: 2, status: "pending", total: 4800 },
];
export const MOCK_GDS_LOGS = [
  { id: "gl1", channel: "Amadeus", action: "ari_push", status: "success", time: `${TODAY} 06:00`, ms: 420 },
  { id: "gl2", channel: "Sabre", action: "res_pull", status: "success", time: `${TODAY} 06:05`, ms: 880 },
  { id: "gl3", channel: "Amadeus", action: "rate_update", status: "partial", time: `${TODAY} 12:00`, ms: 1340 },
];

/* ───────── IoT ───────── */
export const MOCK_IOT_DEVICES = [
  { id: "d1", room: "204", type: "Termostat", vendor: "Nest", online: true, state: "22°C" },
  { id: "d2", room: "204", type: "Aydınlatma", vendor: "Philips Hue", online: true, state: "Açık %60" },
  { id: "d3", room: "305", type: "Perde", vendor: "KNX", online: false, state: "Kapalı" },
  { id: "d4", room: "501", type: "Akıllı Kilit", vendor: "KNX", online: true, state: "Kilitli" },
];
export const MOCK_IOT_SCENES = [
  { id: "sc1", name: "Welcome", trigger: "Check-in", actions: 4, active: true },
  { id: "sc2", name: "Eco", trigger: "Check-out", actions: 3, active: true },
  { id: "sc3", name: "Good Night", trigger: "23:00 zamanlı", actions: 2, active: true },
];

/* ───────── CV Inspection ───────── */
export const MOCK_CV_INSPECTIONS = [
  { id: "ci1", room: "204", model: "YOLOv8-room", score: 92, defects: 1, status: "completed" },
  { id: "ci2", room: "305", model: "YOLOv8-room", score: 76, defects: 3, status: "review" },
  { id: "ci3", room: "118", model: "YOLOv8-room", score: 98, defects: 0, status: "passed" },
];
export const MOCK_CV_DEFECTS = [
  { id: "df1", room: "305", type: "Leke (havlu)", confidence: 0.88, verified: false },
  { id: "df2", room: "305", type: "Eksik minibar", confidence: 0.93, verified: true },
  { id: "df3", room: "204", type: "Kırık abajur", confidence: 0.71, verified: false },
];

/* ───────── Voice ───────── */
export const MOCK_VOICE_INTEGRATIONS = [
  { id: "v1", name: "Alexa for Hospitality", provider: "alexa", rooms: 45, active: true },
  { id: "v2", name: "Google Nest Hub", provider: "google", rooms: 20, active: true },
];
export const MOCK_VOICE_COMMANDS = [
  { id: "vc1", room: "204", intent: "SetTemperature", phrase: "Sıcaklığı 23'e ayarla", result: "success", time: `${TODAY} 15:10` },
  { id: "vc2", room: "305", intent: "RequestTowels", phrase: "Havlu istiyorum", result: "success", time: `${TODAY} 14:45` },
  { id: "vc3", room: "501", intent: "RoomService", phrase: "Kahvaltı sipariş et", result: "forwarded", time: `${TODAY} 08:30` },
];

/* ───────── Multi-Property ───────── */
export const MOCK_CHAIN = { name: "HotelOps Collection", properties: 4 };
export const MOCK_PROPERTIES = [
  { id: "p1", name: "İstanbul Bosphorus", city: "İstanbul", rooms: 180, occupancy: 86, revenue: 4200000 },
  { id: "p2", name: "Antalya Resort", city: "Antalya", rooms: 320, occupancy: 92, revenue: 6800000 },
  { id: "p3", name: "Kapadokya Cave", city: "Nevşehir", rooms: 60, occupancy: 78, revenue: 1900000 },
  { id: "p4", name: "Bodrum Marina", city: "Muğla", rooms: 140, occupancy: 81, revenue: 3100000 },
];

/* ───────── Mobile Check-in ───────── */
export const MOCK_CHECKIN_SESSIONS = [
  { id: "ms1", guest: "Hans Müller", room: "204", ocr: "passed", face: "matched", egm: "submitted", nfc: "issued", status: "completed" },
  { id: "ms2", guest: "Maria Garcia", room: "—", ocr: "passed", face: "pending", egm: "pending", nfc: "—", status: "in_progress" },
  { id: "ms3", guest: "Pierre Dubois", room: "—", ocr: "pending", face: "—", egm: "—", nfc: "—", status: "started" },
];

/* ───────── Blockchain Identity ───────── */
export const MOCK_BLOCKCHAIN_IDS = [
  { id: "b1", guest: "Hans Müller", did: "did:polygon:0x8a3f...e21b", verified: true, credentials: 2 },
  { id: "b2", guest: "Elif Kaya", did: "did:polygon:0x44c1...9f0a", verified: true, credentials: 1 },
  { id: "b3", guest: "John Smith", did: "did:polygon:0x12ab...77cd", verified: false, credentials: 0 },
];
export const MOCK_CREDENTIALS = [
  { id: "vc1", subject: "Hans Müller", type: "LoyaltyTier", issuer: "did:polygon:hotelops", status: "active" },
  { id: "vc2", subject: "Hans Müller", type: "AgeVerification", issuer: "did:polygon:hotelops", status: "active" },
  { id: "vc3", subject: "Elif Kaya", type: "LoyaltyTier", issuer: "did:polygon:hotelops", status: "revoked" },
];

export { TODAY, addDays };
