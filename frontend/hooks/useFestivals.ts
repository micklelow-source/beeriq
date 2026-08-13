"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchFestivals } from "@/services/festivals";

/** Upcoming beer festivals and tastings, curated from beerfests.com. */
export function useFestivals() {
  return useQuery({ queryKey: ["festivals"], queryFn: fetchFestivals });
}
