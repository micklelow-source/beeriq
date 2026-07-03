"use client";

import { FeedList } from "@/components/FeedList";

export default function FeedPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Activity feed</h1>
        <p className="mt-1 text-sm text-neutral-500">
          New beers, events, food trucks, and BrewIQ score changes across all breweries.
        </p>
      </header>
      <FeedList />
    </main>
  );
}
