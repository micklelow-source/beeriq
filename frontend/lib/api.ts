/**
 * Thin typed API client for the BrewIQ backend.
 *
 * Centralises base-URL resolution and error handling so feature code (services /
 * hooks) stays declarative. Kept framework-agnostic and side-effect-free where
 * possible for testability.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Build a fully-qualified API URL with optional query parameters. */
export function buildUrl(
  path: string,
  params?: Record<string, string | number | undefined>,
): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}/api/v1${normalized}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

/** Perform a GET request and parse JSON, throwing {@link ApiError} on failure. */
export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<T> {
  const res = await fetch(buildUrl(path, params), {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new ApiError(`GET ${path} failed`, res.status);
  }
  return (await res.json()) as T;
}

/** Perform a POST request and parse JSON, throwing {@link ApiError} on failure. */
export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiError(`POST ${path} failed`, res.status);
  }
  return (await res.json()) as T;
}
