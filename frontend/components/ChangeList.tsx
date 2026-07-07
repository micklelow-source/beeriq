"use client";

import { EventBadge } from "@/components/EventBadge";
import { useChanges } from "@/hooks/useChanges";
import { formatRelative } from "@/lib/format";

export function ChangeList({ breweryId }: { breweryId: string }) {
  const { data, isLoading } = useChanges(breweryId);

  if (isLoading) return <p className="text-muted-foreground">Loading history…</p>;
  if (!data || data.items.length === 0) {
    return (
      <p className="text-muted-foreground">
        No changes recorded yet. Scrape and extract a tap page to start tracking.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-border">
      {data.items.map((event) => (
        <li key={event.id} className="flex items-center gap-3 py-3">
          <EventBadge type={event.event_type} />
          <span className="flex-1 text-sm text-foreground/90">{event.summary}</span>
          <span className="shrink-0 text-xs text-muted-foreground">
            {formatRelative(event.created_at)}
          </span>
        </li>
      ))}
    </ul>
  );
}
