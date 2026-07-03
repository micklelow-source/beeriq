/** BrewIQ score API service (spec §5). */

import { ApiError, apiGet, apiPost } from "@/lib/api";

export interface ComponentScore {
  name: string;
  value: number | null;
  available: boolean;
  weight: number;
}

export interface Trend {
  direction: "new" | "up" | "down" | "flat";
  delta: number | null;
}

export interface BrewIQScore {
  brewery_id: string;
  overall: number;
  data_confidence: number;
  components: ComponentScore[];
  recommendations: string[];
  trend: Trend;
  computed_at: string;
}

/** Fetch the latest stored score, or null if none has been computed yet. */
export async function fetchScore(id: string): Promise<BrewIQScore | null> {
  try {
    return await apiGet<BrewIQScore>(`/breweries/${id}/score`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

/** Compute (and persist) a fresh score. */
export function computeScore(id: string): Promise<BrewIQScore> {
  return apiPost<BrewIQScore>(`/breweries/${id}/score`);
}
