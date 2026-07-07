/** US state geography helpers: name↔abbreviation, census regions, and colors. */

export type Region = "Northeast" | "Midwest" | "South" | "West";

/** Full state name → USPS abbreviation (us-atlas features carry the full name). */
export const STATE_NAME_TO_ABBR: Record<string, string> = {
  Alabama: "AL", Alaska: "AK", Arizona: "AZ", Arkansas: "AR", California: "CA",
  Colorado: "CO", Connecticut: "CT", Delaware: "DE", "District of Columbia": "DC",
  Florida: "FL", Georgia: "GA", Hawaii: "HI", Idaho: "ID", Illinois: "IL",
  Indiana: "IN", Iowa: "IA", Kansas: "KS", Kentucky: "KY", Louisiana: "LA",
  Maine: "ME", Maryland: "MD", Massachusetts: "MA", Michigan: "MI", Minnesota: "MN",
  Mississippi: "MS", Missouri: "MO", Montana: "MT", Nebraska: "NE", Nevada: "NV",
  "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
  "North Carolina": "NC", "North Dakota": "ND", Ohio: "OH", Oklahoma: "OK",
  Oregon: "OR", Pennsylvania: "PA", "Rhode Island": "RI", "South Carolina": "SC",
  "South Dakota": "SD", Tennessee: "TN", Texas: "TX", Utah: "UT", Vermont: "VT",
  Virginia: "VA", Washington: "WA", "West Virginia": "WV", Wisconsin: "WI",
  Wyoming: "WY",
};

export const ABBR_TO_STATE_NAME: Record<string, string> = Object.fromEntries(
  Object.entries(STATE_NAME_TO_ABBR).map(([name, abbr]) => [abbr, name]),
);

const REGION_STATES: Record<Region, string[]> = {
  Northeast: ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
  Midwest: ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
  South: ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "DC", "WV", "AL", "KY", "MS",
    "TN", "AR", "LA", "OK", "TX"],
  West: ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"],
};

const ABBR_TO_REGION: Record<string, Region> = {};
for (const [region, states] of Object.entries(REGION_STATES) as [Region, string[]][]) {
  for (const s of states) ABBR_TO_REGION[s] = region;
}

export function regionOf(abbr: string): Region | undefined {
  return ABBR_TO_REGION[abbr];
}

/** Base hue per region (used to color-code the map). */
export const REGION_COLORS: Record<Region, string> = {
  Northeast: "#6366f1", // indigo
  Midwest: "#10b981", // emerald
  South: "#f59e0b", // amber
  West: "#ef4444", // red
};

export const REGIONS: Region[] = ["Northeast", "Midwest", "South", "West"];
