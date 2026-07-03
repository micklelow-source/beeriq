/** Change-event (history) API service (spec §4). */

import { apiGet } from "@/lib/api";

export interface ChangeEvent {
  id: string;
  brewery_id: string;
  discovered_url_id: string;
  event_type: string;
  summary: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface ChangeEventPage {
  items: ChangeEvent[];
  total: number;
  limit: number;
  offset: number;
}

export function fetchChanges(
  id: string,
  params?: { limit?: number; offset?: number },
): Promise<ChangeEventPage> {
  return apiGet<ChangeEventPage>(`/breweries/${id}/changes`, params);
}
