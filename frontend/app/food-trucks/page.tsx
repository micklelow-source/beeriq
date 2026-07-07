"use client";

import Link from "next/link";

import { useFoodTrucks } from "@/hooks/useDirectory";

export default function FoodTrucksPage() {
  const { data, isLoading } = useFoodTrucks();

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Food trucks</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Food trucks currently scheduled at tracked breweries.
        </p>
      </header>

      {isLoading && <p className="text-muted-foreground">Loading food trucks…</p>}
      {data && data.length === 0 && (
        <p className="text-muted-foreground">No food trucks listed yet.</p>
      )}

      {data && data.length > 0 && (
        <ul className="divide-y divide-border rounded-xl border border-border bg-card shadow-sm">
          {data.map((t, i) => (
            <li key={`${t.brewery_id}-${t.name}-${i}`} className="flex items-center gap-3 px-4 py-3">
              <span className="text-xl" aria-hidden>
                🚚
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">{t.name}</p>
                <p className="text-sm text-muted-foreground">
                  <Link
                    href={`/breweries/${t.brewery_id}`}
                    className="font-medium text-primary hover:text-primary"
                  >
                    {t.brewery_name}
                  </Link>
                  {t.schedule && <span className="text-muted-foreground"> · {t.schedule}</span>}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
