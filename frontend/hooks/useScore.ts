"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { computeScore, fetchScore } from "@/services/scores";

/** Latest stored BrewIQ score for a brewery (null if never computed). */
export function useScore(id: string) {
  return useQuery({
    queryKey: ["score", id],
    queryFn: () => fetchScore(id),
    enabled: Boolean(id),
  });
}

/** Mutation to (re)compute a brewery's score, refreshing the cached score. */
export function useComputeScore(id: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => computeScore(id),
    onSuccess: (score) => {
      client.setQueryData(["score", id], score);
    },
  });
}
