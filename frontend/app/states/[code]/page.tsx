"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { BreweryCard } from "@/components/BreweryCard";
import { BreweryMap } from "@/components/BreweryMap";
import { useBreweriesByState } from "@/hooks/useBreweriesByState";
import { recencyBucket } from "@/lib/format";
import { ABBR_TO_STATE_NAME } from "@/lib/regions";
import type { Brewery } from "@/services/breweries";

type Category = "all" | "macro" | "micro" | "nano";
type Recency = "any" | "hour" | "24h" | "7d" | "never";
type Sort = "name" | "recent" | "oldest";

const CATEGORY_OF: Record<string, Exclude<Category, "all">> = {
  large: "macro",
  regional: "macro",
  micro: "micro",
  brewpub: "micro",
  nano: "nano",
};

function categoryOf(b: Brewery): Exclude<Category, "all"> | "other" {
  return b.brewery_type ? (CATEGORY_OF[b.brewery_type] ?? "other") : "other";
}

/** Cumulative recency match, mirroring the reference filter semantics. */
function matchesRecency(b: Brewery, r: Recency): boolean {
  if (r === "any") return true;
  const bucket = recencyBucket(b.tap_updated_at);
  if (r === "never") return bucket === "never";
  if (r === "hour") return bucket === "hour";
  if (r === "24h") return bucket === "hour" || bucket === "24h";
  return bucket === "hour" || bucket === "24h" || bucket === "7d"; // 7d
}

function Pill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-sm transition ${
        active
          ? "bg-primary font-medium text-primary-foreground"
          : "border border-border text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

export default function StatePage() {
  const params = useParams<{ code: string }>();
  const code = (params.code ?? "").toUpperCase();
  const stateName = ABBR_TO_STATE_NAME[code] ?? code;
  const { data, isLoading } = useBreweriesByState(code);

  const [category, setCategory] = useState<Category>("all");
  const [recency, setRecency] = useState<Recency>("any");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<Sort>("name");

  const all = useMemo(() => data?.items ?? [], [data]);

  const typeCounts = useMemo(() => {
    const c = { macro: 0, micro: 0, nano: 0 };
    for (const b of all) {
      const cat = categoryOf(b);
      if (cat === "macro") c.macro++;
      else if (cat === "micro") c.micro++;
      else if (cat === "nano") c.nano++;
    }
    return c;
  }, [all]);

  const recencyCounts = useMemo(() => {
    const counts = { any: all.length, hour: 0, "24h": 0, "7d": 0, never: 0 };
    for (const b of all) {
      if (matchesRecency(b, "hour")) counts.hour++;
      if (matchesRecency(b, "24h")) counts["24h"]++;
      if (matchesRecency(b, "7d")) counts["7d"]++;
      if (matchesRecency(b, "never")) counts.never++;
    }
    return counts;
  }, [all]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = all.filter((b) => {
      if (category !== "all" && categoryOf(b) !== category) return false;
      if (!matchesRecency(b, recency)) return false;
      if (q && !`${b.name} ${b.city ?? ""}`.toLowerCase().includes(q)) return false;
      return true;
    });
    const t = (b: Brewery) => (b.tap_updated_at ? new Date(b.tap_updated_at).getTime() : 0);
    rows.sort((a, b) => {
      if (sort === "name") return a.name.localeCompare(b.name);
      if (sort === "recent") return t(b) - t(a);
      return t(a) - t(b);
    });
    return rows;
  }, [all, category, recency, query, sort]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <p className="eyebrow">
        <Link href="/" className="hover:text-foreground">
          United States
        </Link>{" "}
        / {code}
      </p>

      <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-5xl font-bold tracking-tight">{stateName}</h1>
          <p className="mt-2 text-muted-foreground">
            {all.length} breweries tracked · updated live from Open Brewery DB
          </p>
          <Link
            href={`/plan/${code}`}
            className="mt-2 inline-block text-sm font-medium text-primary hover:opacity-80"
          >
            Plan a trip in {stateName} →
          </Link>
        </div>
        <div className="flex gap-6 text-right">
          <Stat label="Macro" value={typeCounts.macro} className="text-destructive" />
          <Stat label="Micro" value={typeCounts.micro} className="text-foreground" />
          <Stat label="Nano" value={typeCounts.nano} className="text-accent" />
        </div>
      </div>

      {/* Category + search */}
      <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          {(["all", "macro", "micro", "nano"] as Category[]).map((c) => (
            <Pill key={c} active={category === c} onClick={() => setCategory(c)}>
              {c === "all" ? "All" : c[0].toUpperCase() + c.slice(1)}
            </Pill>
          ))}
        </div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search brewery or city…"
          className="w-full max-w-xs rounded-lg border border-border bg-input px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none sm:w-64"
        />
      </div>

      {/* Recency + sort */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow mr-1">Tap list updated</span>
          {(
            [
              ["any", "Any", recencyCounts.any],
              ["hour", "Last hour", recencyCounts.hour],
              ["24h", "Last 24h", recencyCounts["24h"]],
              ["7d", "Last 7 days", recencyCounts["7d"]],
              ["never", "Never", recencyCounts.never],
            ] as [Recency, string, number][]
          ).map(([key, label, n]) => (
            <Pill key={key} active={recency === key} onClick={() => setRecency(key)}>
              {label} <span className="ml-1 opacity-60">{n}</span>
            </Pill>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="eyebrow">Sort</span>
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
            className="rounded-lg border border-border bg-input px-2 py-1.5 text-sm text-foreground focus:border-primary focus:outline-none"
          >
            <option value="name">Name (A–Z)</option>
            <option value="recent">Recently updated</option>
            <option value="oldest">Oldest updated</option>
          </select>
        </label>
      </div>

      {isLoading && <p className="mt-8 text-muted-foreground">Loading breweries…</p>}

      {!isLoading && filtered.length > 0 && (
        <div className="mt-6">
          <BreweryMap breweries={filtered} />
        </div>
      )}

      {!isLoading && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((b) => (
            <BreweryCard key={b.id} brewery={b} />
          ))}
        </div>
      )}
      {!isLoading && filtered.length === 0 && (
        <p className="mt-8 text-muted-foreground">No breweries match these filters.</p>
      )}
    </main>
  );
}

function Stat({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div>
      <p className={`font-serif text-2xl font-bold ${className}`}>{value}</p>
      <p className="eyebrow">{label}</p>
    </div>
  );
}
