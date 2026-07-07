"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchBreweries } from "@/services/breweries";

/** All breweries in a given state (USPS abbreviation). */
export function useBreweriesByState(state: string) {
  return useQuery({
    queryKey: ["breweries-by-state", state],
    queryFn: () => fetchBreweries({ state, limit: 200 }),
    enabled: Boolean(state),
  });
}
