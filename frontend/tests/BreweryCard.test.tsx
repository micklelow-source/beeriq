import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BreweryCard } from "@/components/BreweryCard";
import type { Brewery } from "@/services/breweries";

const brewery: Brewery = {
  id: "1",
  name: "Stoneface Brewing",
  slug: "stoneface-brewing",
  website: "https://stonefacebrewing.com",
  brewery_type: "micro",
  city: "Newington",
  state: "NH",
  latitude: null,
  longitude: null,
  created_at: "",
  updated_at: "",
  tap_updated_at: null,
};

describe("BreweryCard", () => {
  it("renders name (linking to detail), type, location, and tap-list recency", () => {
    render(<BreweryCard brewery={brewery} />);
    const nameLink = screen.getByRole("link", { name: "Stoneface Brewing" });
    expect(nameLink.getAttribute("href")).toBe("/breweries/1");
    expect(screen.getByText("Microbrewery")).toBeDefined();
    expect(screen.getByText("Newington, NH")).toBeDefined();
    // Never scraped → "NEVER" recency label.
    expect(screen.getByText(/tap list · never/i)).toBeDefined();
  });
});
