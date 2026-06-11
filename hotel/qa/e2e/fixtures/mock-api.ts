import { Page } from "@playwright/test";

/**
 * Backend API yanıtlarını mock'lar.
 * front-office.spec.ts'de route.fulfill() ile kullanılır.
 */
export const MOCK_ARRIVALS = [
  {
    id: "arr-001",
    guest_name: "Ahmet Yılmaz",
    room_type: "DBL",
    check_in: "2026-06-11",
    check_out: "2026-06-14",
    status: "arriving",
  },
  {
    id: "arr-002",
    guest_name: "Ayşe Kaya",
    room_type: "SUI",
    check_in: "2026-06-11",
    check_out: "2026-06-13",
    status: "arriving",
  },
];

export const MOCK_DEPARTURES = [
  {
    id: "dep-001",
    guest_name: "Mehmet Demir",
    room_no: "101",
    check_out: "2026-06-11",
    balance: 0,
    status: "departing",
  },
];

export const MOCK_ROOMS = [
  { room_number: "101", floor: 1, status: "clean", room_type: "DBL" },
  { room_number: "102", floor: 1, status: "dirty", room_type: "DBL" },
  { room_number: "201", floor: 2, status: "occupied", room_type: "SUI" },
  { room_number: "202", floor: 2, status: "out_of_order", room_type: "SUI" },
];

export const MOCK_BOARD = {
  data: MOCK_ROOMS.map((r) => ({
    room_no: r.room_number,
    floor: r.floor,
    status: r.status,
    room_type: r.room_type,
    active_task: null,
    current_guest: r.status === "occupied",
  })),
  meta: {
    counts: {
      clean: 1,
      dirty: 1,
      occupied: 1,
      out_of_order: 1,
    },
  },
};

/**
 * Backend API çağrılarını mock'lamak için setup.
 * Test fixture'ında kullanılır.
 */
export async function setupMockApi(page: Page) {
  await page.route("**/api/v1/front-office/reservations/arrivals**", (route) =>
    route.fulfill({ json: MOCK_ARRIVALS })
  );
  await page.route("**/api/v1/front-office/reservations/departures**", (route) =>
    route.fulfill({ json: MOCK_DEPARTURES })
  );
  await page.route("**/api/v1/front-office/rooms**", (route) =>
    route.fulfill({ json: MOCK_ROOMS })
  );
  await page.route("**/api/v1/housekeeping/board**", (route) =>
    route.fulfill({ json: MOCK_BOARD })
  );
}
