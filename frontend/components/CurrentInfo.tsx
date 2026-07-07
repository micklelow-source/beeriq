"use client";

import { useCurrent } from "@/hooks/useCurrent";
import type { Beer } from "@/services/current";

function BeerRow({ beer }: { beer: Beer }) {
  return (
    <li className="flex items-start justify-between gap-3 py-2">
      <div className="min-w-0">
        <p className="font-medium text-foreground">
          {beer.name}
          {beer.seasonal && (
            <span className="ml-2 rounded bg-primary/15 px-1.5 py-0.5 text-xs text-primary">
              seasonal
            </span>
          )}
          {beer.limited && (
            <span className="ml-1 rounded bg-destructive/15 px-1.5 py-0.5 text-xs text-destructive">
              limited
            </span>
          )}
        </p>
        {beer.style && <p className="text-sm text-muted-foreground">{beer.style}</p>}
      </div>
      <div className="shrink-0 text-right text-sm tabular-nums text-muted-foreground">
        {beer.abv != null && <span className="text-foreground/80">{beer.abv}% ABV</span>}
        {beer.ibu != null && <span className="ml-2 opacity-70">{beer.ibu} IBU</span>}
      </div>
    </li>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-3 font-serif text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function CurrentInfo({ breweryId }: { breweryId: string }) {
  const { data, isLoading } = useCurrent(breweryId);

  if (isLoading) return <p className="text-muted-foreground">Loading current data…</p>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <Panel title={`On tap${data.beers.length ? ` (${data.beers.length})` : ""}`}>
        {data.beers.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No tap list extracted yet — run a scrape + AI extraction on this brewery.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {data.beers.map((b) => (
              <BeerRow key={b.name} beer={b} />
            ))}
          </ul>
        )}
        {(data.hours || data.amenities.length > 0) && (
          <div className="mt-4 border-t border-border pt-3 text-sm text-muted-foreground">
            {data.hours && (
              <p>
                <span className="opacity-70">Hours:</span> {data.hours}
              </p>
            )}
            {data.amenities.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {data.amenities.map((a) => (
                  <span key={a} className="rounded-full bg-muted px-2 py-0.5 text-xs">
                    {a}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </Panel>

      <div className="grid gap-6 sm:grid-cols-2">
        <Panel title="Events">
          {data.events.length === 0 ? (
            <p className="text-sm text-muted-foreground">No events listed.</p>
          ) : (
            <ul className="space-y-2">
              {data.events.map((e) => (
                <li key={e.title} className="text-sm">
                  <span className="font-medium text-foreground">{e.title}</span>
                  {e.date && <span className="text-muted-foreground"> · {e.date}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Food trucks">
          {data.food_trucks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No food trucks listed.</p>
          ) : (
            <ul className="space-y-2">
              {data.food_trucks.map((t) => (
                <li key={t.name} className="text-sm">
                  <span className="font-medium text-foreground">{t.name}</span>
                  {t.schedule && <span className="text-muted-foreground"> · {t.schedule}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}
