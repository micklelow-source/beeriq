"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { ChangeList } from "@/components/ChangeList";
import { ScoreCard } from "@/components/ScoreCard";
import { useBrewery } from "@/hooks/useBrewery";

export default function BreweryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: brewery, isLoading, isError } = useBrewery(id);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <Link href="/" className="text-sm text-neutral-500 hover:text-brew-600">
        ← All breweries
      </Link>

      {isLoading && <p className="mt-6 text-neutral-500">Loading…</p>}
      {isError && <p className="mt-6 text-red-600">Brewery not found.</p>}

      {brewery && (
        <>
          <header className="mb-8 mt-4">
            <h1 className="text-3xl font-bold tracking-tight">{brewery.name}</h1>
            <p className="mt-1 text-neutral-500">
              {[brewery.city, brewery.state].filter(Boolean).join(", ")}
              {brewery.website && (
                <>
                  {" · "}
                  <a
                    href={brewery.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brew-600 hover:text-brew-500"
                  >
                    {new URL(brewery.website).host}
                  </a>
                </>
              )}
            </p>
          </header>

          <div className="grid gap-6 lg:grid-cols-2">
            <ScoreCard breweryId={id} />
            <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold">Change history</h2>
              <ChangeList breweryId={id} />
            </section>
          </div>
        </>
      )}
    </main>
  );
}
