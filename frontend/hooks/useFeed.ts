"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchFeed } from "@/services/feed";

/** The cross-brewery activity feed. */
export function useFeed(limit = 25) {
  return useQuery({
    queryKey: ["feed", { limit }],
    queryFn: () => fetchFeed({ limit }),
    refetchInterval: 15_000,
  });
}
