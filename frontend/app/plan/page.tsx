"use client";

import { UsMap } from "@/components/UsMap";

export default function PlanLandingPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8 text-center">
        <p className="eyebrow">Plan a Trip</p>
        <h1 className="mt-1 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
          Where does the journey begin?
        </h1>
        <p className="mt-2 text-muted-foreground">
          Pick a state on the map. Then drop breweries onto your itinerary and get driving times
          between each stop.
        </p>
      </header>
      <UsMap basePath="/plan" />
    </main>
  );
}
