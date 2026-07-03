import Link from "next/link";

import type { Brewery } from "@/services/breweries";

/** Presentational card for a single brewery. */
export function BreweryCard({ brewery }: { brewery: Brewery }) {
  const location = [brewery.city, brewery.state].filter(Boolean).join(", ");
  return (
    <article className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm transition hover:border-brew-500/40 hover:shadow">
      <h2 className="text-lg font-semibold text-neutral-900">
        <Link href={`/breweries/${brewery.id}`} className="hover:text-brew-600">
          {brewery.name}
        </Link>
      </h2>
      {location && <p className="text-sm text-neutral-500">{location}</p>}
      <div className="mt-2 flex items-center gap-4 text-sm">
        <Link
          href={`/breweries/${brewery.id}`}
          className="font-medium text-brew-600 hover:text-brew-500"
        >
          View score →
        </Link>
        {brewery.website && (
          <a
            href={brewery.website}
            target="_blank"
            rel="noreferrer"
            className="text-neutral-400 hover:text-neutral-600"
          >
            Website ↗
          </a>
        )}
      </div>
    </article>
  );
}
