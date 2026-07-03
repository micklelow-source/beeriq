import Link from "next/link";

/** Top navigation shared across pages. */
export function NavBar() {
  return (
    <header className="border-b border-neutral-200 bg-white">
      <nav className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <Link href="/" className="text-lg font-bold tracking-tight">
          Brew<span className="text-brew-600">IQ</span>
        </Link>
        <div className="flex gap-4 text-sm text-neutral-600">
          <Link href="/" className="hover:text-brew-600">
            Breweries
          </Link>
          <Link href="/feed" className="hover:text-brew-600">
            Feed
          </Link>
        </div>
      </nav>
    </header>
  );
}
