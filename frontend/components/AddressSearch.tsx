"use client";

import { useEffect, useRef, useState } from "react";

const GOOGLE_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

/** URL that opens Google Maps searching for breweries near an address (no key). */
function mapsSearchUrl(address: string): string {
  const query = encodeURIComponent(`breweries near ${address}`);
  return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
  }
}

/**
 * Address lookup that ties to Google Maps.
 *
 * - Always: submitting opens Google Maps to "breweries near <address>".
 * - If NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is set: upgrades the input to Google Places
 *   autocomplete. Inert (link-only) until a key is provided.
 */
export function AddressSearch() {
  const [address, setAddress] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!GOOGLE_KEY || typeof window === "undefined") return;

    const initAutocomplete = () => {
      if (!window.google || !inputRef.current) return;
      const ac = new window.google.maps.places.Autocomplete(inputRef.current, {
        types: ["geocode"],
        fields: ["formatted_address"],
      });
      ac.addListener("place_changed", () => {
        const place = ac.getPlace();
        if (place?.formatted_address) setAddress(place.formatted_address);
      });
    };

    if (window.google?.maps?.places) {
      initAutocomplete();
      return;
    }
    const id = "google-maps-places";
    if (document.getElementById(id)) return;
    const script = document.createElement("script");
    script.id = id;
    script.async = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_KEY}&libraries=places`;
    script.onload = initAutocomplete;
    document.head.appendChild(script);
  }, []);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim()) window.open(mapsSearchUrl(address.trim()), "_blank", "noreferrer");
  };

  return (
    <form onSubmit={submit} className="flex w-full max-w-xl gap-2">
      <input
        ref={inputRef}
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="Find breweries near an address…"
        className="flex-1 rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
        aria-label="Address"
      />
      <button
        type="submit"
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
      >
        Search
      </button>
    </form>
  );
}
