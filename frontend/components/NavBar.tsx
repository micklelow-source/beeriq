import Link from "next/link";

/** Top navigation modeled on the BeerIQ reference design. */
export function NavBar() {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary font-serif text-lg font-bold text-primary-foreground">
            B
          </span>
          <span className="leading-none">
            <span className="block font-serif text-lg font-bold text-foreground">BeerIQ</span>
            <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Brewery Intelligence
            </span>
          </span>
        </Link>

        <div className="flex items-center gap-5 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-foreground">
            Map
          </Link>
          <Link href="/plan" className="hover:text-foreground">
            Plan a Trip
          </Link>
          <Link href="/events" className="hidden hover:text-foreground sm:inline">
            Events
          </Link>
          <Link href="/food-trucks" className="hidden hover:text-foreground sm:inline">
            Food Trucks
          </Link>
          <Link href="/feed" className="hidden hover:text-foreground sm:inline">
            Feed
          </Link>
          <button className="rounded-lg bg-primary px-4 py-1.5 font-medium text-primary-foreground hover:opacity-90">
            Sign in
          </button>
        </div>
      </nav>
    </header>
  );
}
