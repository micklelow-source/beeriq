import Link from "next/link";

import { recencyBucket, recencyDot, recencyLabel } from "@/lib/format";
import type { Brewery } from "@/services/breweries";

const TYPE_LABELS: Record<string, string> = {
  micro: "Microbrewery",
  nano: "Nanobrewery",
  regional: "Regional Brewery",
  brewpub: "Brewpub",
  large: "Macrobrewery",
  planning: "In Planning",
  bar: "Bar",
  contract: "Contract Brewery",
  proprietor: "Proprietor",
  closed: "Closed",
};

/** Brewery card modeled on the BeerIQ reference design. */
export function BreweryCard({ brewery }: { brewery: Brewery }) {
  const location = [brewery.city, brewery.state].filter(Boolean).join(", ");
  const typeLabel = brewery.brewery_type
    ? (TYPE_LABELS[brewery.brewery_type] ?? brewery.brewery_type)
    : null;
  const bucket = recencyBucket(brewery.tap_updated_at);

  return (
    <article className="flex flex-col rounded-xl border border-border bg-card p-5 transition hover:border-primary/40">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-serif text-lg font-semibold leading-tight text-card-foreground">
          <Link href={`/breweries/${brewery.id}`} className="hover:text-primary">
            {brewery.name}
          </Link>
        </h3>
        <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${recencyDot(bucket)}`} />
      </div>

      {typeLabel && <p className="eyebrow mt-1">{typeLabel}</p>}

      <div className="mt-3 text-sm text-muted-foreground">
        {location && <p className="text-foreground/80">{location}</p>}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="flex items-center gap-1.5 rounded-full border border-border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
          <span className={`h-1.5 w-1.5 rounded-full ${recencyDot(bucket)}`} />
          Tap list · {recencyLabel(brewery.tap_updated_at)}
        </span>
        <Link
          href={`/breweries/${brewery.id}`}
          className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground hover:text-primary"
        >
          View →
        </Link>
      </div>
    </article>
  );
}
