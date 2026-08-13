"use client";

import Link from "next/link";

import { useEvents } from "@/hooks/useDirectory";
import { useFestivals } from "@/hooks/useFestivals";

function formatFestivalDate(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric", year: "numeric" });
}

export default function EventsPage() {
  const { data, isLoading } = useEvents();
  const { data: festivals, isLoading: festivalsLoading } = useFestivals();

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Events</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upcoming events across all tracked breweries.
        </p>
      </header>

      {isLoading && <p className="text-muted-foreground">Loading events…</p>}
      {data && data.length === 0 && (
        <p className="text-muted-foreground">No events listed yet.</p>
      )}

      {data && data.length > 0 && (
        <ul className="divide-y divide-border rounded-xl border border-border bg-card shadow-sm">
          {data.map((e, i) => (
            <li key={`${e.brewery_id}-${e.title}-${i}`} className="px-4 py-3">
              <p className="font-medium text-foreground">{e.title}</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {e.date && <span>{e.date} · </span>}
                <Link
                  href={`/breweries/${e.brewery_id}`}
                  className="font-medium text-primary hover:text-primary"
                >
                  {e.brewery_name}
                </Link>
                {e.brewery_state && <span className="text-muted-foreground"> · {e.brewery_state}</span>}
              </p>
              {e.description && <p className="mt-1 text-sm text-muted-foreground">{e.description}</p>}
            </li>
          ))}
        </ul>
      )}

      <header className="mb-6 mt-12">
        <h2 className="text-xl font-bold tracking-tight">Beer Festivals & Tastings</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Curated from{" "}
          <a
            href="https://beerfests.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary hover:text-primary"
          >
            beerfests.com
          </a>
          .
        </p>
      </header>

      {festivalsLoading && <p className="text-muted-foreground">Loading festivals…</p>}
      {festivals && festivals.length === 0 && (
        <p className="text-muted-foreground">No upcoming festivals listed yet.</p>
      )}

      {festivals && festivals.length > 0 && (
        <ul className="divide-y divide-border rounded-xl border border-border bg-card shadow-sm">
          {festivals.map((f) => (
            <li key={f.id} className="px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <p className="font-medium text-foreground">
                  {f.url ? (
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-primary"
                    >
                      {f.name}
                    </a>
                  ) : (
                    f.name
                  )}
                </p>
                {f.category === "tasting" && (
                  <span className="whitespace-nowrap rounded-full bg-primary/15 px-2 py-0.5 text-xs font-medium text-primary">
                    Tasting
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {formatFestivalDate(f.event_date) && <span>{formatFestivalDate(f.event_date)} · </span>}
                {[f.city, f.state].filter(Boolean).join(", ")}
              </p>
              {f.description && <p className="mt-1 text-sm text-muted-foreground">{f.description}</p>}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
