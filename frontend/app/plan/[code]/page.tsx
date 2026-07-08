"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { TripMap } from "@/components/TripMap";
import { useBreweriesByState } from "@/hooks/useBreweriesByState";
import {
  driveEstimate,
  formatMiles,
  formatMinutes,
  haversineMiles,
  type LatLng,
  nearestNeighborOrder,
} from "@/lib/geo";
import { ABBR_TO_STATE_NAME } from "@/lib/regions";
import type { Brewery } from "@/services/breweries";

function coordsOf(b: Brewery): LatLng | null {
  return b.latitude != null && b.longitude != null
    ? { lat: b.latitude, lng: b.longitude }
    : null;
}

type Leg = { miles: number; minutes: number } | { unknown: true } | null;

export default function PlanStatePage() {
  const params = useParams<{ code: string }>();
  const code = (params.code ?? "").toUpperCase();
  const stateName = ABBR_TO_STATE_NAME[code] ?? code;
  const { data, isLoading } = useBreweriesByState(code);

  const [route, setRoute] = useState<Brewery[]>([]);
  const [query, setQuery] = useState("");

  const inRoute = useMemo(() => new Set(route.map((b) => b.id)), [route]);
  const available = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (data?.items ?? []).filter(
      (b) =>
        !inRoute.has(b.id) &&
        (!q || `${b.name} ${b.city ?? ""}`.toLowerCase().includes(q)),
    );
  }, [data, inRoute, query]);

  const legs: Leg[] = route.map((b, i) => {
    if (i === 0) return null;
    const a = coordsOf(route[i - 1]);
    const c = coordsOf(b);
    if (!a || !c) return { unknown: true };
    return driveEstimate(haversineMiles(a, c));
  });

  const total = { miles: 0, minutes: 0 };
  for (const l of legs) {
    if (l && !("unknown" in l)) {
      total.miles += l.miles;
      total.minutes += l.minutes;
    }
  }

  const routeCoords = useMemo(
    () => route.map(coordsOf).filter((p): p is LatLng => p != null),
    [route],
  );

  const allCoords = useMemo(
    () => (data?.items ?? []).map(coordsOf).filter((p): p is LatLng => p != null),
    [data],
  );

  const mapsUrl = useMemo(() => {
    const pts = routeCoords;
    if (pts.length < 2) return null;
    const origin = pts[0];
    const dest = pts[pts.length - 1];
    const way = pts.slice(1, -1).map((p) => `${p.lat},${p.lng}`).join("|");
    const base = `https://www.google.com/maps/dir/?api=1&origin=${origin.lat},${origin.lng}&destination=${dest.lat},${dest.lng}`;
    return way ? `${base}&waypoints=${encodeURIComponent(way)}` : base;
  }, [routeCoords]);

  const move = (i: number, dir: -1 | 1) =>
    setRoute((r) => {
      const j = i + dir;
      if (j < 0 || j >= r.length) return r;
      const copy = [...r];
      [copy[i], copy[j]] = [copy[j], copy[i]];
      return copy;
    });

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <Link href="/plan" className="text-sm text-muted-foreground hover:text-primary">
        ← Pick another state
      </Link>
      <header className="mb-6 mt-3">
        <p className="eyebrow">Plan a Trip</p>
        <h1 className="mt-1 font-serif text-4xl font-bold tracking-tight">{stateName}</h1>
        <p className="mt-1 text-muted-foreground">
          Add breweries to build your route. Driving times are straight-line estimates.
        </p>
      </header>

      <div className="mb-6">
        <TripMap stops={routeCoords} allCoords={allCoords} stateName={stateName} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Picker */}
        <section className="rounded-xl border border-border bg-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-serif text-lg font-semibold">Breweries</h2>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search…"
              className="rounded-lg border border-border bg-input px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
            />
          </div>
          {isLoading && <p className="text-muted-foreground">Loading…</p>}
          <ul className="max-h-[28rem] divide-y divide-border overflow-auto">
            {available.map((b) => (
              <li key={b.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <p className="truncate font-medium text-foreground">{b.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {b.city ?? "—"}
                    {!coordsOf(b) && <span className="ml-1 opacity-60">· no map location</span>}
                  </p>
                </div>
                <button
                  onClick={() => setRoute((r) => [...r, b])}
                  className="shrink-0 rounded-lg border border-border px-2.5 py-1 text-sm text-muted-foreground hover:border-primary hover:text-primary"
                >
                  + Add
                </button>
              </li>
            ))}
          </ul>
        </section>

        {/* Itinerary */}
        <section className="rounded-xl border border-border bg-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-serif text-lg font-semibold">
              Your itinerary{route.length ? ` (${route.length})` : ""}
            </h2>
            {route.length > 0 && (
              <div className="flex gap-2 text-xs">
                <button
                  onClick={() => setRoute((r) => nearestNeighborOrder(r))}
                  className="rounded-lg border border-border px-2 py-1 text-muted-foreground hover:text-primary"
                >
                  Optimize
                </button>
                <button
                  onClick={() => setRoute([])}
                  className="rounded-lg border border-border px-2 py-1 text-muted-foreground hover:text-destructive"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {route.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Add breweries from the left to build your route.
            </p>
          ) : (
            <>
              <ol className="space-y-1">
                {route.map((b, i) => (
                  <li key={b.id}>
                    {i > 0 && (
                      <div className="flex items-center gap-2 py-1 pl-3 text-xs text-muted-foreground">
                        <span className="text-primary">↓</span>
                        {legs[i] && "unknown" in legs[i]!
                          ? "distance unknown"
                          : legs[i] && !("unknown" in legs[i]!)
                            ? `${formatMiles((legs[i] as { miles: number }).miles)} · ${formatMinutes((legs[i] as { minutes: number }).minutes)}`
                            : ""}
                      </div>
                    )}
                    <div className="flex items-center gap-3 rounded-lg border border-border px-3 py-2">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                        {i + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium text-foreground">{b.name}</p>
                        <p className="text-xs text-muted-foreground">{b.city ?? "—"}</p>
                      </div>
                      <div className="flex shrink-0 items-center gap-1 text-muted-foreground">
                        <button
                          onClick={() => move(i, -1)}
                          disabled={i === 0}
                          className="px-1 hover:text-foreground disabled:opacity-30"
                          aria-label="Move up"
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => move(i, 1)}
                          disabled={i === route.length - 1}
                          className="px-1 hover:text-foreground disabled:opacity-30"
                          aria-label="Move down"
                        >
                          ↓
                        </button>
                        <button
                          onClick={() => setRoute((r) => r.filter((x) => x.id !== b.id))}
                          className="px-1 hover:text-destructive"
                          aria-label="Remove"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>

              <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                <p className="text-sm text-muted-foreground">
                  Est. total:{" "}
                  <span className="font-medium text-foreground">
                    {formatMiles(total.miles)} · {formatMinutes(total.minutes)}
                  </span>
                </p>
                {mapsUrl && (
                  <a
                    href={mapsUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
                  >
                    Open in Google Maps ↗
                  </a>
                )}
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
