"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStateStats } from "@/services/stats";

/** Per-state brewery counts, keyed by USPS abbreviation. */
export function useStateStats() {
  return useQuery({
    queryKey: ["state-stats"],
    queryFn: fetchStateStats,
    select: (rows) => {
      const map: Record<string, number> = {};
      for (const row of rows) map[row.state] = row.count;
      return map;
    },
    staleTime: 60_000,
  });
}

/** Per-state counts of breweries with at least one recorded tap list, keyed
 * by USPS abbreviation. Shares useStateStats' query cache (same key/fetcher). */
export function useStateTapStats() {
  return useQuery({
    queryKey: ["state-stats"],
    queryFn: fetchStateStats,
    select: (rows) => {
      const map: Record<string, number> = {};
      for (const row of rows) map[row.state] = row.with_taps;
      return map;
    },
    staleTime: 60_000,
  });
}
