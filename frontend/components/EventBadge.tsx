import { humanizeType } from "@/lib/format";

const COLORS: Record<string, string> = {
  beer_added: "bg-green-100 text-green-700",
  beer_removed: "bg-red-100 text-red-700",
  beer_abv_changed: "bg-amber-100 text-amber-700",
  beer_description_changed: "bg-amber-100 text-amber-700",
  event_added: "bg-blue-100 text-blue-700",
  event_removed: "bg-neutral-100 text-neutral-600",
  food_truck_added: "bg-orange-100 text-orange-700",
  food_truck_removed: "bg-neutral-100 text-neutral-600",
  hours_changed: "bg-purple-100 text-purple-700",
  score_increase: "bg-brew-500/10 text-brew-600",
};

/** A small colored badge for a change-event / feed-item type. */
export function EventBadge({ type }: { type: string }) {
  const cls = COLORS[type] ?? "bg-neutral-100 text-neutral-600";
  return (
    <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {humanizeType(type)}
    </span>
  );
}
