"use client";

import { AddressSearch } from "@/components/AddressSearch";
import { DashboardStats } from "@/components/DashboardStats";
import { UsMap } from "@/components/UsMap";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">
          Brew<span className="text-brew-600">IQ</span> dashboard
        </h1>
        <p className="mt-1 text-neutral-500">
          Live tap lists, events, food trucks, and brewery scores across the US.
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
          <h2 className="text-lg font-semibold">Explore by state</h2>
          <p className="text-sm text-neutral-500">Click a state to see its breweries</p>
        </div>
        <UsMap />
      </section>
    </main>
  );
}
