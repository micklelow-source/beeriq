import { humanizeType } from "@/lib/format";

const COLORS: Record<string, string> = {
  beer_added: "bg-green-500/15 text-green-400",
  beer_removed: "bg-red-500/15 text-red-400",
  beer_abv_changed: "bg-amber-500/15 text-amber-300",
  beer_description_changed: "bg-amber-500/15 text-amber-300",
  event_added: "bg-blue-500/15 text-blue-300",
  event_removed: "bg-muted text-muted-foreground",
  food_truck_added: "bg-orange-500/15 text-orange-300",
  food_truck_removed: "bg-muted text-muted-foreground",
  hours_changed: "bg-purple-500/15 text-purple-300",
  score_increase: "bg-primary/15 text-primary",
};

/** A small colored badge for a change-event / feed-item type. */
export function EventBadge({ type }: { type: string }) {
  const cls = COLORS[type] ?? "bg-muted text-muted-foreground";
  return (
    <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {humanizeType(type)}
    </span>
  );
}
