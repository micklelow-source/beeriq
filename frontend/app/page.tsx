"use client";

import { BreweryCard } from "@/components/BreweryCard";
import { useBreweries } from "@/hooks/useBreweries";

export default function HomePage() {
  const { data, isLoading, isError } = useBreweries("NH");

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Brew<span className="text-brew-600">IQ</span>
        </h1>
        <p className="mt-1 text-neutral-500">
          New Hampshire breweries, live tap lists, and scores.
        </p>
      </header>

      {isLoading && <p className="text-neutral-500">Loading breweries…</p>}
      {isError && (
        <p className="text-red-600">
          Could not load breweries. Is the API running?
        </p>
      )}

      {data && (
        <>
          <p className="mb-4 text-sm text-neutral-500">
            {data.total} {data.total === 1 ? "brewery" : "breweries"}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((brewery) => (
              <BreweryCard key={brewery.id} brewery={brewery} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
