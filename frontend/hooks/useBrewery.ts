"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchBrewery } from "@/services/breweries";

/** React Query hook for a single brewery by id. */
export function useBrewery(id: string) {
  return useQuery({
    queryKey: ["brewery", id],
    queryFn: () => fetchBrewery(id),
    enabled: Boolean(id),
  });
}
