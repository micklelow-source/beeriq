"use client";

import { useEvents, useFoodTrucks } from "@/hooks/useDirectory";
import { useFeed } from "@/hooks/useFeed";
import { useStateStats } from "@/hooks/useStateStats";

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="eyebrow">{label}</p>
      <p className="mt-1 font-serif text-3xl font-bold tabular-nums text-primary">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function DashboardStats() {
  const { data: counts } = useStateStats();
  const { data: events } = useEvents();
  const { data: trucks } = useFoodTrucks();
  const { data: feed } = useFeed();

  const total = counts ? Object.values(counts).reduce((a, b) => a + b, 0) : 0;
  const states = counts ? Object.keys(counts).length : 0;

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <StatCard label="Breweries" value={String(total)} hint={`${states} state(s)`} />
      <StatCard label="Active events" value={String(events?.length ?? 0)} />
      <StatCard label="Food trucks" value={String(trucks?.length ?? 0)} />
      <StatCard
        label="Recent activity"
        value={String(feed?.total ?? 0)}
        hint="more analytics soon"
      />
    </div>
  );
}
