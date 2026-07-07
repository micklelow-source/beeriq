/** Cross-brewery events and food-truck listings (spec §8). */

import { apiGet } from "@/lib/api";

interface BreweryRef {
  brewery_id: string;
  brewery_name: string;
  brewery_slug: string;
  brewery_state: string | null;
}

export interface DirectoryEvent extends BreweryRef {
  title: string;
  date: string | null;
  description: string | null;
}

export interface DirectoryFoodTruck extends BreweryRef {
  name: string;
  schedule: string | null;
}

export function fetchDirectoryEvents(): Promise<DirectoryEvent[]> {
  return apiGet<DirectoryEvent[]>("/events");
}

export function fetchDirectoryFoodTrucks(): Promise<DirectoryFoodTruck[]> {
  return apiGet<DirectoryFoodTruck[]>("/food-trucks");
}
