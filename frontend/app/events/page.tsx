"use client";

import Link from "next/link";

import { useEvents } from "@/hooks/useDirectory";

export default function EventsPage() {
  const { data, isLoading } = useEvents();

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
    </main>
  );
}
