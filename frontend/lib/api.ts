export const API =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Monitor = {
  id: number;
  name: string;
  slug: string;
  url: string;
  method: string;
  interval_seconds: number;
  is_active: boolean;
  is_public: boolean;
  current_status: "up" | "down" | "degraded" | "pending";
  last_checked_at: string | null;
  uptime_24h: number | null;
  avg_latency_ms: number | null;
};

export type Check = {
  checked_at: string;
  status_code: number | null;
  latency_ms: number | null;
  ok: boolean;
  error: string | null;
};

export type Incident = {
  id: number;
  monitor_id: number;
  monitor_name: string | null;
  started_at: string;
  resolved_at: string | null;
  cause: string;
  summary: string | null;
  acknowledged: boolean;
};

export function token(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("vigil_token");
}

export function saveSession(t: string, handle: string) {
  window.localStorage.setItem("vigil_token", t);
  window.localStorage.setItem("vigil_handle", handle);
}

export function clearSession() {
  window.localStorage.removeItem("vigil_token");
  window.localStorage.removeItem("vigil_handle");
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init.headers as Record<string, string>) ?? {}),
  };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;

  const res = await fetch(`${API}${path}`, { ...init, headers, cache: "no-store" });
  if (res.status === 401) {
    clearSession();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Session expired.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status}).`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export function relativeTime(iso: string | null): string {
  if (!iso) return "never";
  const then = new Date(iso.endsWith("Z") ? iso : `${iso}Z`).getTime();
  const seconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86400)}d ago`;
}
