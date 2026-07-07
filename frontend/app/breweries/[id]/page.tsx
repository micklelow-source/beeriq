"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { ChangeList } from "@/components/ChangeList";
import { CurrentInfo } from "@/components/CurrentInfo";
import { ScoreCard } from "@/components/ScoreCard";
import { useBrewery } from "@/hooks/useBrewery";

function mapsDirectionsUrl(query: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

export default function BreweryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: brewery, isLoading, isError } = useBrewery(id);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <Link href="/" className="text-sm text-muted-foreground hover:text-primary">
        ← Dashboard
      </Link>

      {isLoading && <p className="mt-6 text-muted-foreground">Loading…</p>}
      {isError && <p className="mt-6 text-destructive">Brewery not found.</p>}

      {brewery && (
        <>
          <header className="mb-8 mt-4">
            <h1 className="text-3xl font-bold tracking-tight">{brewery.name}</h1>
            <p className="mt-1 flex flex-wrap items-center gap-x-2 text-muted-foreground">
              <span>{[brewery.city, brewery.state].filter(Boolean).join(", ")}</span>
              {brewery.website && (
                <>
                  <span className="text-border">·</span>
                  <a
                    href={brewery.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:text-primary"
                  >
                    Website ↗
                  </a>
                </>
              )}
              <span className="text-border">·</span>
              <a
                href={mapsDirectionsUrl(
                  [brewery.name, brewery.city, brewery.state].filter(Boolean).join(" "),
                )}
                target="_blank"
                rel="noreferrer"
                className="text-primary hover:text-primary"
              >
                Directions ↗
              </a>
            </p>
          </header>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-6">
              <ScoreCard breweryId={id} />
              <CurrentInfo breweryId={id} />
            </div>
            <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold">Change history</h2>
              <ChangeList breweryId={id} />
            </section>
          </div>
        </>
      )}
    </main>
  );
}
