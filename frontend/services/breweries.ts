/** Brewery API service — mirrors the backend's Pydantic schemas. */

import { apiGet } from "@/lib/api";

export interface Brewery {
  id: string;
  name: string;
  slug: string;
  website: string | null;
  brewery_type: string | null;
  city: string | null;
  state: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  updated_at: string;
  tap_updated_at: string | null;
}

export interface BreweryPage {
  items: Brewery[];
  total: number;
  limit: number;
  offset: number;
}

export function fetchBreweries(params?: {
  state?: string;
  limit?: number;
  offset?: number;
}): Promise<BreweryPage> {
  return apiGet<BreweryPage>("/breweries", params);
}

export function fetchBrewery(id: string): Promise<Brewery> {
  return apiGet<Brewery>(`/breweries/${id}`);
}
