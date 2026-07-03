"use client";

import { useScore, useComputeScore } from "@/hooks/useScore";
import { humanizeType, scoreColor } from "@/lib/format";
import type { ComponentScore, Trend } from "@/services/scores";

function TrendBadge({ trend }: { trend: Trend }) {
  const map: Record<Trend["direction"], { label: string; cls: string }> = {
    up: { label: `▲ ${trend.delta ?? ""}`, cls: "bg-green-100 text-green-700" },
    down: { label: `▼ ${trend.delta ?? ""}`, cls: "bg-red-100 text-red-700" },
    flat: { label: "— flat", cls: "bg-neutral-100 text-neutral-500" },
    new: { label: "new", cls: "bg-brew-500/10 text-brew-600" },
  };
  const { label, cls } = map[trend.direction];
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>{label}</span>
  );
}

function ComponentBar({ component }: { component: ComponentScore }) {
  const value = component.value ?? 0;
  return (
    <li className="flex items-center gap-3">
      <span className="w-40 shrink-0 text-sm text-neutral-600">
        {humanizeType(component.name)}
      </span>
      <span className="h-2 flex-1 overflow-hidden rounded-full bg-neutral-100">
        {component.available ? (
          <span
            className="block h-full rounded-full bg-brew-500"
            style={{ width: `${value}%` }}
          />
        ) : null}
      </span>
      <span className="w-16 shrink-0 text-right text-xs tabular-nums text-neutral-500">
        {component.available ? value.toFixed(0) : "no data"}
      </span>
    </li>
  );
}

export function ScoreCard({ breweryId }: { breweryId: string }) {
  const { data: score, isLoading } = useScore(breweryId);
  const compute = useComputeScore(breweryId);

  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">BrewIQ Score</h2>
        <button
          onClick={() => compute.mutate()}
          disabled={compute.isPending}
          className="rounded-md bg-brew-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brew-500 disabled:opacity-60"
        >
          {compute.isPending ? "Computing…" : score ? "Recompute" : "Compute score"}
        </button>
      </div>

      {isLoading && <p className="text-neutral-500">Loading…</p>}

      {!isLoading && !score && (
        <p className="text-neutral-500">
          No score yet — compute one from the latest discovery, scrape, and extraction data.
        </p>
      )}

      {score && (
        <>
          <div className="mb-5 flex items-end gap-3">
            <span className={`text-5xl font-bold tabular-nums ${scoreColor(score.overall)}`}>
              {score.overall.toFixed(0)}
            </span>
            <span className="pb-1 text-neutral-400">/ 100</span>
            <span className="pb-2">
              <TrendBadge trend={score.trend} />
            </span>
            <span className="ml-auto pb-2 text-xs text-neutral-500">
              {Math.round(score.data_confidence * 100)}% data confidence
            </span>
          </div>

          <ul className="space-y-2">
            {score.components.map((c) => (
              <ComponentBar key={c.name} component={c} />
            ))}
          </ul>

          {score.recommendations.length > 0 && (
            <div className="mt-5 border-t border-neutral-100 pt-4">
              <h3 className="mb-2 text-sm font-medium text-neutral-700">Recommendations</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-600">
                {score.recommendations.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
