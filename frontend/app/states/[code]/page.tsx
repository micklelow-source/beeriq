"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { BreweryCard } from "@/components/BreweryCard";
import { useBreweriesByState } from "@/hooks/useBreweriesByState";
import { ABBR_TO_STATE_NAME, REGION_COLORS, regionOf } from "@/lib/regions";

export default function StatePage() {
  const params = useParams<{ code: string }>();
  const code = (params.code ?? "").toUpperCase();
  const stateName = ABBR_TO_STATE_NAME[code] ?? code;
  const region = regionOf(code);
  const { data, isLoading } = useBreweriesByState(code);

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <Link href="/" className="text-sm text-neutral-500 hover:text-brew-600">
        ← Back to map
      </Link>

      <header className="mb-8 mt-4 flex items-center gap-3">
        <h1 className="text-3xl font-bold tracking-tight">{stateName}</h1>
        {region && (
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
            style={{ backgroundColor: REGION_COLORS[region] }}
          >
            {region}
          </span>
        )}
      </header>

      {isLoading && <p className="text-neutral-500">Loading breweries…</p>}

      {data && data.items.length === 0 && (
        <p className="text-neutral-500">
          No breweries tracked in {stateName} yet. Import them via Open Brewery DB to get started.
        </p>
      )}

      {data && data.items.length > 0 && (
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
