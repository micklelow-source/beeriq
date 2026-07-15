/** Per-state brewery counts for the US map. */

import { apiGet } from "@/lib/api";

export interface StateStat {
  state: string;
  count: number;
  with_taps: number;
}

export function fetchStateStats(): Promise<StateStat[]> {
  return apiGet<StateStat[]>("/breweries/stats/by-state");
}
