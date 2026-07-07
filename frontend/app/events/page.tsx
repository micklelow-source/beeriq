"use client";

import Link from "next/link";

import { useEvents } from "@/hooks/useDirectory";

export default function EventsPage() {
  const { data, isLoading } = useEvents();

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Events</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Upcoming events across all tracked breweries.
        </p>
      </header>

      {isLoading && <p className="text-neutral-500">Loading events…</p>}
      {data && data.length === 0 && (
        <p className="text-neutral-500">No events listed yet.</p>
      )}

      {data && data.length > 0 && (
        <ul className="divide-y divide-neutral-100 rounded-xl border border-neutral-200 bg-white shadow-sm">
          {data.map((e, i) => (
            <li key={`${e.brewery_id}-${e.title}-${i}`} className="px-4 py-3">
              <p className="font-medium text-neutral-900">{e.title}</p>
              <p className="mt-0.5 text-sm text-neutral-500">
                {e.date && <span>{e.date} · </span>}
                <Link
                  href={`/breweries/${e.brewery_id}`}
                  className="font-medium text-brew-600 hover:text-brew-500"
                >
                  {e.brewery_name}
                </Link>
                {e.brewery_state && <span className="text-neutral-400"> · {e.brewery_state}</span>}
              </p>
              {e.description && <p className="mt-1 text-sm text-neutral-600">{e.description}</p>}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
