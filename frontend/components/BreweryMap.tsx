"use client";

import { useEffect, useRef, useState } from "react";

import "leaflet/dist/leaflet.css";
import { BreweryCard } from "@/components/BreweryCard";
import { recencyBucket } from "@/lib/format";
import type { Brewery } from "@/services/breweries";

// Same hues as the recency dot elsewhere in the app (globals.css): accent =
// fresh (green), primary = amber, muted-foreground = stale/never.
function pinColor(bucket: ReturnType<typeof recencyBucket>): string {
  if (bucket === "hour" || bucket === "24h") return "oklch(60% 0.18 145)";
  if (bucket === "7d") return "oklch(78% 0.16 70)";
  return "oklch(72% 0.03 80)";
}

/**
 * Plots breweries with known coordinates on a keyless Leaflet + OSM map.
 * Hovering a pin shows its name; clicking one selects it and shows a full
 * BreweryCard below the map.
 */
export function BreweryMap({ breweries }: { breweries: Brewery[] }) {
  const divRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layerRef = useRef<any>(null);
  const [selected, setSelected] = useState<Brewery | null>(null);

  const located = breweries.filter(
    (b): b is Brewery & { latitude: number; longitude: number } =>
      b.latitude != null && b.longitude != null,
  );

  useEffect(() => {
    // Selection only makes sense while its brewery is still in view.
    if (selected && !located.some((b) => b.id === selected.id)) {
      setSelected(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [breweries]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !divRef.current) return;

      if (!mapRef.current) {
        mapRef.current = L.map(divRef.current, { scrollWheelZoom: false });
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: "© OpenStreetMap",
        }).addTo(mapRef.current);
      }
      const map = mapRef.current;
      if (layerRef.current) map.removeLayer(layerRef.current);
      const group = L.layerGroup().addTo(map);
      layerRef.current = group;

      located.forEach((b) => {
        const color = pinColor(recencyBucket(b.tap_updated_at));
        const marker = L.circleMarker([b.latitude, b.longitude], {
          radius: 7,
          color: "oklch(18% 0.02 60)",
          weight: 1.5,
          fillColor: color,
          fillOpacity: 0.9,
        }).addTo(group);
        marker.bindTooltip(b.name, { direction: "top", offset: [0, -6] });
        marker.on("click", () => setSelected(b));
      });

      if (located.length) {
        map.fitBounds(
          L.latLngBounds(located.map((b) => [b.latitude, b.longitude] as [number, number])),
          { padding: [30, 30], maxZoom: 12 },
        );
      } else {
        map.setView([39.8, -98.6], 4);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [located.map((b) => b.id).join(",")]);

  useEffect(
    () => () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    },
    [],
  );

  return (
    <div>
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <div ref={divRef} className="h-[380px] w-full" />
        <p className="px-4 py-2 text-xs text-muted-foreground">
          {located.length
            ? `${located.length} brewer${located.length === 1 ? "y" : "ies"} shown · hover for name, click for details`
            : "No mapped locations for the current filters."}
        </p>
      </div>

      {selected && (
        <div className="mt-4 max-w-sm">
          <div className="mb-2 flex items-center justify-between">
            <span className="eyebrow">Selected brewery</span>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Clear ✕
            </button>
          </div>
          <BreweryCard brewery={selected} />
        </div>
      )}
    </div>
  );
}
