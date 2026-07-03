"use client";

import Link from "next/link";

import { EventBadge } from "@/components/EventBadge";
import { useFeed } from "@/hooks/useFeed";
import { formatRelative } from "@/lib/format";
import type { FeedItem } from "@/services/feed";

function badgeType(item: FeedItem): string {
  if (item.kind === "score_increase") return "score_increase";
  const t = item.details?.["event_type"];
  return typeof t === "string" ? t : "beer_added";
}

export function FeedList() {
  const { data, isLoading, isError } = useFeed();

  if (isLoading) return <p className="text-neutral-500">Loading feed…</p>;
  if (isError) return <p className="text-red-600">Could not load the feed.</p>;
  if (!data || data.items.length === 0) {
    return (
      <p className="text-neutral-500">
        Nothing here yet — activity appears as breweries update their taps, events, and scores.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-neutral-100 rounded-xl border border-neutral-200 bg-white shadow-sm">
      {data.items.map((item) => (
        <li key={item.id} className="flex items-center gap-3 px-4 py-3">
          <EventBadge type={item.kind === "score_increase" ? "score_increase" : badgeType(item)} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm text-neutral-800">{item.summary}</p>
            <Link
              href={`/breweries/${item.brewery_id}`}
              className="text-xs font-medium text-brew-600 hover:text-brew-500"
            >
              {item.brewery_name}
            </Link>
          </div>
          <span className="shrink-0 text-xs text-neutral-400">
            {formatRelative(item.created_at)}
          </span>
        </li>
      ))}
    </ul>
  );
}
