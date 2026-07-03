import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BreweryCard } from "@/components/BreweryCard";
import type { Brewery } from "@/services/breweries";

const brewery: Brewery = {
  id: "1",
  name: "Stoneface Brewing",
  slug: "stoneface-brewing",
  website: "https://stonefacebrewing.com",
  city: "Newington",
  state: "NH",
  latitude: null,
  longitude: null,
  created_at: "",
  updated_at: "",
};

describe("BreweryCard", () => {
  it("renders name, location, and links to the detail page and website", () => {
    render(<BreweryCard brewery={brewery} />);
    expect(screen.getByRole("heading", { name: "Stoneface Brewing" })).toBeDefined();
    expect(screen.getByText("Newington, NH")).toBeDefined();

    const detail = screen.getByRole("link", { name: /view score/i });
    expect(detail.getAttribute("href")).toBe("/breweries/1");

    const website = screen.getByRole("link", { name: /website/i });
    expect(website.getAttribute("href")).toBe("https://stonefacebrewing.com");
  });
});
