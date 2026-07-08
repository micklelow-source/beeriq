"use client";

import { useEffect, useRef } from "react";

import "leaflet/dist/leaflet.css";
import type { LatLng } from "@/lib/geo";

const GOOGLE_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
const AMBER = "#e89b3c";

const pt = (p: LatLng) => `${p.lat},${p.lng}`;

/** Official Google Maps Embed API URL (requires a key). */
function embedApiUrl(stops: LatLng[], stateName: string): string {
  if (stops.length >= 2) {
    const waypoints = stops.slice(1, -1).map(pt).join("|");
    const wp = waypoints ? `&waypoints=${encodeURIComponent(waypoints)}` : "";
    return `https://www.google.com/maps/embed/v1/directions?key=${GOOGLE_KEY}&origin=${pt(
      stops[0],
    )}&destination=${pt(stops[stops.length - 1])}${wp}&mode=driving`;
  }
  if (stops.length === 1) {
    return `https://www.google.com/maps/embed/v1/place?key=${GOOGLE_KEY}&q=${pt(stops[0])}&zoom=11`;
  }
  return `https://www.google.com/maps/embed/v1/search?key=${GOOGLE_KEY}&q=${encodeURIComponent(
    `breweries in ${stateName}`,
  )}`;
}

/**
 * Live route map for the trip planner.
 *
 * - With NEXT_PUBLIC_GOOGLE_MAPS_API_KEY set: the official Google Maps Embed API
 *   (Google requires a key to embed a live map).
 * - Without a key: an interactive Leaflet + OpenStreetMap map that draws the same
 *   route (markers + polyline), so the planner always shows a working map. The
 *   "Open in Google Maps" link on the itinerary still works keyless.
 */
export function TripMap({
  stops,
  allCoords = [],
  stateName,
}: {
  stops: LatLng[];
  allCoords?: LatLng[];
  stateName: string;
}) {
  const divRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layerRef = useRef<any>(null);

  useEffect(() => {
    if (GOOGLE_KEY) return; // iframe path renders the Google map
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

      if (stops.length >= 2) {
        L.polyline(
          stops.map((p) => [p.lat, p.lng]),
          { color: AMBER, weight: 3, opacity: 0.9 },
        ).addTo(group);
      }
      if (stops.length) {
        stops.forEach((p, i) => {
          L.marker([p.lat, p.lng], {
            icon: L.divIcon({
              className: "",
              html: `<div style="background:${AMBER};color:#2a1e12;font-weight:700;width:22px;height:22px;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-size:12px;border:2px solid #1c1714">${i + 1}</div>`,
              iconSize: [22, 22],
              iconAnchor: [11, 11],
            }),
          }).addTo(group);
        });
      } else {
        allCoords.forEach((p) =>
          L.circleMarker([p.lat, p.lng], {
            radius: 4,
            color: AMBER,
            weight: 1,
            fillOpacity: 0.6,
          }).addTo(group),
        );
      }

      const pts = stops.length ? stops : allCoords;
      if (pts.length) {
        map.fitBounds(
          L.latLngBounds(pts.map((p) => [p.lat, p.lng] as [number, number])),
          { padding: [30, 30], maxZoom: 12 },
        );
      } else {
        map.setView([39.8, -98.6], 4);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [stops, allCoords]);

  useEffect(
    () => () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    },
    [],
  );

  if (GOOGLE_KEY) {
    return (
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <iframe
          title="Trip map"
          src={embedApiUrl(stops, stateName)}
          className="h-[380px] w-full"
          style={{ border: 0 }}
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
        />
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div ref={divRef} className="h-[380px] w-full" />
      <p className="px-4 py-2 text-xs text-muted-foreground">
        {stops.length === 0
          ? `Breweries in ${stateName} — add stops to draw your route.`
          : "Route preview · set NEXT_PUBLIC_GOOGLE_MAPS_API_KEY for a live Google Map."}
      </p>
    </div>
  );
}
