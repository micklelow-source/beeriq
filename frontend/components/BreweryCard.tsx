import type { Brewery } from "@/services/breweries";

/** Presentational card for a single brewery. */
export function BreweryCard({ brewery }: { brewery: Brewery }) {
  const location = [brewery.city, brewery.state].filter(Boolean).join(", ");
  return (
    <article className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-neutral-900">{brewery.name}</h2>
      {location && <p className="text-sm text-neutral-500">{location}</p>}
      {brewery.website && (
        <a
          href={brewery.website}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-sm font-medium text-brew-600 hover:text-brew-500"
        >
          Visit website →
        </a>
      )}
    </article>
  );
}
