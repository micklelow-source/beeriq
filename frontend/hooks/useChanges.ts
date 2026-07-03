"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchChanges } from "@/services/changes";

/** A brewery's change history (newest first). */
export function useChanges(id: string) {
  return useQuery({
    queryKey: ["changes", id],
    queryFn: () => fetchChanges(id, { limit: 50 }),
    enabled: Boolean(id),
  });
}
