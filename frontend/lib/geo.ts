/** Client-side geo helpers for the trip planner (straight-line estimates). */

export interface LatLng {
  lat: number;
  lng: number;
}

/** Great-circle distance in miles between two points. */
export function haversineMiles(a: LatLng, b: LatLng): number {
  const R = 3958.8;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

/**
 * Rough driving estimate from a straight-line distance: apply a road-winding
 * factor and an average speed. A real routing API (Google Directions) would
 * replace this — see the NEXT_PUBLIC_GOOGLE_MAPS_API_KEY note.
 */
export function driveEstimate(straightMiles: number): { miles: number; minutes: number } {
  const roadMiles = straightMiles * 1.3;
  const minutes = (roadMiles / 45) * 60;
  return { miles: roadMiles, minutes };
}

export function formatMiles(miles: number): string {
  return `${miles.toFixed(1)} mi`;
}

export function formatMinutes(minutes: number): string {
  const m = Math.round(minutes);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem ? `${h}h ${rem}m` : `${h}h`;
}

/** Nearest-neighbor ordering starting from the first item (route optimization). */
export function nearestNeighborOrder<T extends { latitude: number | null; longitude: number | null }>(
  items: T[],
): T[] {
  const withCoords = items.filter((i) => i.latitude != null && i.longitude != null);
  const without = items.filter((i) => i.latitude == null || i.longitude == null);
  if (withCoords.length <= 2) return items;

  const remaining = [...withCoords];
  const ordered: T[] = [remaining.shift()!];
  while (remaining.length) {
    const last = ordered[ordered.length - 1];
    const from: LatLng = { lat: last.latitude!, lng: last.longitude! };
    let bestIdx = 0;
    let bestDist = Infinity;
    remaining.forEach((cand, idx) => {
      const d = haversineMiles(from, { lat: cand.latitude!, lng: cand.longitude! });
      if (d < bestDist) {
        bestDist = d;
        bestIdx = idx;
      }
    });
    ordered.push(remaining.splice(bestIdx, 1)[0]);
  }
  return [...ordered, ...without];
}
