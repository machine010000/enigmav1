export type ApiResult<T> = { data: T | null; error: string | null };

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getApiBaseUrl(): string {
  return apiBaseUrl.replace(/\/$/, "");
}

export async function apiRequest<T>(path: string, init: RequestInit = {}, onUnauthorized?: () => void): Promise<T> {
  if (!apiBaseUrl) throw new ApiError(0, "Backend configuration is missing. Set NEXT_PUBLIC_API_BASE_URL.");
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: { Accept: "application/json", ...init.headers } });
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    if (response.status === 401) { onUnauthorized?.(); throw new ApiError(401, payload?.detail ?? "Your session has expired."); }
    if (!response.ok) throw new ApiError(response.status, payload?.detail ?? `Request failed with status ${response.status}.`);
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, "The backend is unavailable.");
  }
}