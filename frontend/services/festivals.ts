/** Curated beer festivals and tastings, sourced from beerfests.com. */

import { apiGet } from "@/lib/api";

export interface Festival {
  id: string;
  slug: string;
  name: string;
  category: "festival" | "tasting";
  event_date: string | null;
  city: string | null;
  state: string | null;
  description: string | null;
  url: string | null;
  source: string;
}

export function fetchFestivals(): Promise<Festival[]> {
  return apiGet<Festival[]>("/festivals");
}
