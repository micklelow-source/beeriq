"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchCurrent } from "@/services/current";

/** Current tap list / events / food trucks for a brewery. */
export function useCurrent(breweryId: string) {
  return useQuery({
    queryKey: ["current", breweryId],
    queryFn: () => fetchCurrent(breweryId),
    enabled: Boolean(breweryId),
  });
}
