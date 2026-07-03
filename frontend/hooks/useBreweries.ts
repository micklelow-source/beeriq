"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchBreweries } from "@/services/breweries";

/** React Query hook returning a page of breweries, optionally filtered by state. */
export function useBreweries(state?: string) {
  return useQuery({
    queryKey: ["breweries", { state }],
    queryFn: () => fetchBreweries({ state, limit: 100 }),
    staleTime: 30_000,
  });
}
