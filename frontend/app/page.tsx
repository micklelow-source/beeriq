"use client";

import { AddressSearch } from "@/components/AddressSearch";
import { DashboardStats } from "@/components/DashboardStats";
import { UsMap } from "@/components/UsMap";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <header className="mb-8">
        <p className="eyebrow">Brewery Intelligence</p>
        <h1 className="mt-1 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
          Every brewery in America, <span className="text-primary">live</span>.
        </h1>
        <p className="mt-2 max-w-2xl text-muted-foreground">
          Live tap lists, events, food trucks, and BeerIQ scores — explore by state or plan a
          trip.
        </p>
      </header>

      <div className="mb-8">
        <AddressSearch />
      </div>

      <section className="mb-10">
        <DashboardStats />
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="font-serif text-xl font-semibold">Explore by state</h2>
          <p className="text-sm text-muted-foreground">Click a state to see its breweries</p>
        </div>
        <UsMap />
      </section>
    </main>
  );
}
