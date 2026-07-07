/** Small presentation helpers shared across components. */

/** Format an ISO timestamp as a compact relative time (e.g. "3h ago"). */
export function formatRelative(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

/** Human label for a change-event / feed-item type. */
export function humanizeType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/** Tailwind classes for a score value, red→amber→green. */
export function scoreColor(value: number): string {
  if (value >= 70) return "text-accent";
  if (value >= 40) return "text-primary";
  return "text-destructive";
}

export type RecencyBucket = "hour" | "24h" | "7d" | "older" | "never";

/** Bucket a tap-list update time to match the recency filter in the design. */
export function recencyBucket(iso: string | null): RecencyBucket {
  if (!iso) return "never";
  const hours = (Date.now() - new Date(iso).getTime()) / 3.6e6;
  if (hours < 1) return "hour";
  if (hours < 24) return "24h";
  if (hours < 24 * 7) return "7d";
  return "older";
}

/** Short uppercase label for a tap-list update time (e.g. "NEVER", "2H AGO"). */
export function recencyLabel(iso: string | null): string {
  return iso ? formatRelative(iso).toUpperCase() : "NEVER";
}

/** Dot color class for a recency bucket. */
export function recencyDot(bucket: RecencyBucket): string {
  if (bucket === "hour" || bucket === "24h") return "bg-accent";
  if (bucket === "7d") return "bg-primary";
  return "bg-muted-foreground/40";
}
