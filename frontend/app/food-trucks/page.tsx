"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useFoodTrucks } from "@/hooks/useDirectory";
import { ABBR_TO_STATE_NAME, REGIONS, regionOf, type Region } from "@/lib/regions";
import type { DirectoryFoodTruck } from "@/services/directory";

const UNKNOWN_REGION = "Other" as const;

function groupByRegionThenState(
  trucks: DirectoryFoodTruck[],
): Map<Region | typeof UNKNOWN_REGION, Map<string, DirectoryFoodTruck[]>> {
  const byRegion = new Map<Region | typeof UNKNOWN_REGION, Map<string, DirectoryFoodTruck[]>>();

  for (const truck of trucks) {
    const state = truck.brewery_state ?? "";
    const region = regionOf(state) ?? UNKNOWN_REGION;

    if (!byRegion.has(region)) byRegion.set(region, new Map());
    const byState = byRegion.get(region)!;

    if (!byState.has(state)) byState.set(state, []);
    byState.get(state)!.push(truck);
  }

  return byRegion;
}

export default function FoodTrucksPage() {
  const { data, isLoading } = useFoodTrucks();

  const grouped = useMemo(() => groupByRegionThenState(data ?? []), [data]);
  const regionOrder: (Region | typeof UNKNOWN_REGION)[] = [...REGIONS, UNKNOWN_REGION];

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Food trucks</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Food trucks currently scheduled at tracked breweries, grouped by region and state.
        </p>
      </header>

      {isLoading && <p className="text-muted-foreground">Loading food trucks…</p>}
      {data && data.length === 0 && (
        <p className="text-muted-foreground">No food trucks listed yet.</p>
      )}

      {data && data.length > 0 && (
        <div className="space-y-8">
          {regionOrder
            .filter((region) => grouped.has(region))
            .map((region) => {
              const byState = grouped.get(region)!;
              const stateCodes = [...byState.keys()].sort();
              return (
                <section key={region}>
                  <h2 className="mb-3 text-lg font-semibold text-foreground">{region}</h2>
                  <div className="space-y-5">
                    {stateCodes.map((stateCode) => (
                      <div key={stateCode || "unknown"}>
                        <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                          {stateCode ? (ABBR_TO_STATE_NAME[stateCode] ?? stateCode) : "Unknown state"}
                        </h3>
                        <ul className="divide-y divide-border rounded-xl border border-border bg-card shadow-sm">
                          {byState.get(stateCode)!.map((t, i) => (
                            <li
                              key={`${t.brewery_id}-${t.name}-${i}`}
                              className="flex items-center gap-3 px-4 py-3"
                            >
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
                                  {t.schedule && (
                                    <span className="text-muted-foreground"> · {t.schedule}</span>
                                  )}
                                </p>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </section>
              );
            })}
        </div>
      )}
    </main>
  );
}
