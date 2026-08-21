export type ApiResult<T> = { data: T | null; error: string | null };

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ?? "";
const apiBaseUrl = configuredApiBaseUrl || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

export class ApiError extends Error {
  status: number;
  detail: string;
  code?: string;
  existingJobId?: string;

  constructor(status: number, detail: string, metadata?: { code?: string; existingJobId?: string }) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = metadata?.code;
    this.existingJobId = metadata?.existingJobId;
  }
}

export function parseApiErrorPayload(payload: unknown, fallback: string): { message: string; code?: string; existingJobId?: string } {
  if (!payload || typeof payload !== "object") return { message: fallback };
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return { message: detail };
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const structured = detail as { code?: unknown; existing_job_id?: unknown; message?: unknown };
    return {
      message: typeof structured.message === "string" ? structured.message : fallback,
      code: typeof structured.code === "string" ? structured.code : undefined,
      existingJobId: typeof structured.existing_job_id === "string" ? structured.existing_job_id : undefined,
    };
  }
  if (Array.isArray(detail)) return { message: "Some submitted fields are invalid." };
  return { message: fallback };
}

export function getApiBaseUrl(): string {
  return apiBaseUrl.replace(/\/$/, "");
}

export async function apiRequest<T>(path: string, init: RequestInit = {}, onUnauthorized?: () => void): Promise<T> {
  if (!apiBaseUrl) throw new ApiError(0, "Backend configuration is missing. Set NEXT_PUBLIC_API_BASE_URL.");
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: { Accept: "application/json", ...init.headers } });
    const payload = await response.json().catch(() => null) as unknown;
    const fallback = `Request failed with status ${response.status}.`;
    const failure = parseApiErrorPayload(payload, fallback);
    if (response.status === 401) { onUnauthorized?.(); throw new ApiError(401, failure.message === fallback ? "Your session has expired." : failure.message, failure); }
    if (!response.ok) throw new ApiError(response.status, failure.message, failure);
    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, "The backend is unavailable.");
  }
}
