/** Live activity feed API service (spec §8). */

import { apiGet } from "@/lib/api";

export interface FeedItem {
  id: string;
  kind: "change_event" | "score_increase";
  brewery_id: string;
  brewery_name: string;
  brewery_slug: string;
  summary: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface FeedPage {
  items: FeedItem[];
  total: number;
  limit: number;
  offset: number;
}

export function fetchFeed(params?: {
  limit?: number;
  offset?: number;
}): Promise<FeedPage> {
  return apiGet<FeedPage>("/feed", params);
}
