"use client";

import { geoAlbersUsa, geoPath } from "d3-geo";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import { useRouter } from "next/navigation";
import { feature } from "topojson-client";

import { useStateStats } from "@/hooks/useStateStats";
import { REGION_COLORS, REGIONS, regionOf, STATE_NAME_TO_ABBR } from "@/lib/regions";
import statesData from "us-atlas/states-10m.json";

// us-atlas states-10m carries geographic (lon/lat) coordinates, so project them
// onto the 975×610 canvas with the composite AlbersUSA projection (AK/HI insets).
const VIEW_W = 975;
const VIEW_H = 610;
type StateProps = { name: string };
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const topology = statesData as any;
const collection = feature(
  topology,
  topology.objects.states,
) as unknown as FeatureCollection<Geometry, StateProps>;
const projection = geoAlbersUsa().fitSize([VIEW_W, VIEW_H], collection);
const pathGen = geoPath(projection);

export function UsMap() {
  const router = useRouter();
  const { data: counts = {} } = useStateStats();

  const go = (abbr: string) => router.push(`/states/${abbr}`);

  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm">
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="h-auto w-full"
        role="img"
        aria-label="US brewery map"
      >
        <g>
          {collection.features.map((f: Feature<Geometry, StateProps>) => {
            const abbr = STATE_NAME_TO_ABBR[f.properties.name];
            if (!abbr) return null;
            const region = regionOf(abbr);
            const count = counts[abbr] ?? 0;
            const color = region ? REGION_COLORS[region] : "#9ca3af";
            return (
              <path
                key={String(f.id)}
                d={pathGen(f) ?? undefined}
                className={`state ${count > 0 ? "active" : ""}`}
                style={{ fill: color }}
                onClick={() => go(abbr)}
                role="button"
                aria-label={`${f.properties.name}: ${count} breweries`}
              >
                <title>{`${f.properties.name}${count > 0 ? ` — ${count} breweries` : ""}`}</title>
              </path>
            );
          })}
        </g>
      </svg>

      <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-xs text-neutral-600">
        {REGIONS.map((r) => (
          <span key={r} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-sm"
              style={{ backgroundColor: REGION_COLORS[r] }}
            />
            {r}
          </span>
        ))}
        <span className="text-neutral-400">· shaded = has breweries · click to explore</span>
      </div>

      <style jsx>{`
        .state {
          fill-opacity: 0.16;
          stroke: #ffffff;
          stroke-width: 0.5;
          cursor: pointer;
          transition: fill-opacity 0.15s, stroke 0.15s;
          outline: none;
        }
        .state.active {
          fill-opacity: 0.85;
        }
        .state:hover {
          fill-opacity: 1;
          stroke: #1f2937;
          stroke-width: 1;
        }
      `}</style>
    </div>
  );
}
