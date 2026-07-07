"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchDirectoryEvents, fetchDirectoryFoodTrucks } from "@/services/directory";

/** All current events across breweries. */
export function useEvents() {
  return useQuery({ queryKey: ["directory-events"], queryFn: fetchDirectoryEvents });
}

/** All current food trucks across breweries. */
export function useFoodTrucks() {
  return useQuery({
    queryKey: ["directory-food-trucks"],
    queryFn: fetchDirectoryFoodTrucks,
  });
}
