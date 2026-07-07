/** Current tap list / events / food trucks for a brewery (spec §8). */

import { apiGet } from "@/lib/api";

export interface Beer {
  name: string;
  style: string | null;
  abv: number | null;
  ibu: number | null;
  availability: string | null;
  description: string | null;
  seasonal: boolean;
  limited: boolean;
}

export interface CurrentEvent {
  title: string;
  date: string | null;
  description: string | null;
}

export interface CurrentFoodTruck {
  name: string;
  schedule: string | null;
}

export interface CurrentData {
  beers: Beer[];
  events: CurrentEvent[];
  food_trucks: CurrentFoodTruck[];
  hours: string | null;
  amenities: string[];
}

export function fetchCurrent(breweryId: string): Promise<CurrentData> {
  return apiGet<CurrentData>(`/breweries/${breweryId}/current`);
}
