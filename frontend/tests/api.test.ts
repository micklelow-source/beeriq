import { describe, expect, it } from "vitest";

import { buildUrl } from "@/lib/api";

describe("buildUrl", () => {
  it("prefixes the API version and normalizes leading slash", () => {
    expect(buildUrl("breweries")).toContain("/api/v1/breweries");
    expect(buildUrl("/breweries")).toContain("/api/v1/breweries");
  });

  it("appends defined query params and skips undefined ones", () => {
    const url = new URL(buildUrl("/breweries", { state: "NH", limit: 50, offset: undefined }));
    expect(url.searchParams.get("state")).toBe("NH");
    expect(url.searchParams.get("limit")).toBe("50");
    expect(url.searchParams.has("offset")).toBe(false);
  });
});
