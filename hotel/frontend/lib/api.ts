/**
 * API istemci sarmalayıcısı — backend sözleşmesi (docs/02 §15).
 * Liste yanıtları: { data: [...], meta: { page, per_page, total, total_pages } }
 * Hata yanıtları:  { error: { code, message, details } }
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ListMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ListResponse<T> {
  data: T[];
  meta: ListMeta;
}

export interface ApiError {
  error: { code: string; message: string; details?: Record<string, unknown> };
}

export class ApiRequestError extends Error {
  constructor(public status: number, public body: ApiError) {
    super(body.error?.message ?? `HTTP ${status}`);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({ error: { code: "UNKNOWN", message: res.statusText } }))) as ApiError;
    throw new ApiRequestError(res.status, body);
  }
  return res.json() as Promise<T>;
}
