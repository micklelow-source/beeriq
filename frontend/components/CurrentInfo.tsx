"use client";

import { useCurrent } from "@/hooks/useCurrent";
import type { Beer } from "@/services/current";

function BeerRow({ beer }: { beer: Beer }) {
  return (
    <li className="flex items-start justify-between gap-3 py-2">
      <div className="min-w-0">
        <p className="font-medium text-neutral-900">
          {beer.name}
          {beer.seasonal && (
            <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700">
              seasonal
            </span>
          )}
          {beer.limited && (
            <span className="ml-1 rounded bg-red-100 px-1.5 py-0.5 text-xs text-red-700">
              limited
            </span>
          )}
        </p>
        {beer.style && <p className="text-sm text-neutral-500">{beer.style}</p>}
      </div>
      <div className="shrink-0 text-right text-sm text-neutral-600 tabular-nums">
        {beer.abv != null && <span>{beer.abv}% ABV</span>}
        {beer.ibu != null && <span className="ml-2 text-neutral-400">{beer.ibu} IBU</span>}
      </div>
    </li>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function CurrentInfo({ breweryId }: { breweryId: string }) {
  const { data, isLoading } = useCurrent(breweryId);

  if (isLoading) return <p className="text-neutral-500">Loading current data…</p>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <Panel title={`On tap${data.beers.length ? ` (${data.beers.length})` : ""}`}>
        {data.beers.length === 0 ? (
          <p className="text-sm text-neutral-500">
            No tap list extracted yet — run a scrape + AI extraction on this brewery.
          </p>
        ) : (
          <ul className="divide-y divide-neutral-100">
            {data.beers.map((b) => (
              <BeerRow key={b.name} beer={b} />
            ))}
          </ul>
        )}
        {(data.hours || data.amenities.length > 0) && (
          <div className="mt-4 border-t border-neutral-100 pt-3 text-sm text-neutral-600">
            {data.hours && (
              <p>
                <span className="text-neutral-400">Hours:</span> {data.hours}
              </p>
            )}
            {data.amenities.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {data.amenities.map((a) => (
                  <span key={a} className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs">
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
            <p className="text-sm text-neutral-500">No events listed.</p>
          ) : (
            <ul className="space-y-2">
              {data.events.map((e) => (
                <li key={e.title} className="text-sm">
                  <span className="font-medium text-neutral-900">{e.title}</span>
                  {e.date && <span className="text-neutral-500"> · {e.date}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Food trucks">
          {data.food_trucks.length === 0 ? (
            <p className="text-sm text-neutral-500">No food trucks listed.</p>
          ) : (
            <ul className="space-y-2">
              {data.food_trucks.map((t) => (
                <li key={t.name} className="text-sm">
                  <span className="font-medium text-neutral-900">{t.name}</span>
                  {t.schedule && <span className="text-neutral-500"> · {t.schedule}</span>}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}
