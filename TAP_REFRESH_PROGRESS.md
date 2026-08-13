# Nationwide tap-list refresh progress (East → West)

Started 2026-08-13. Each row = one `scrape_taps.py --state XX` run against the
shared local dev DB (`backend/var/brewiq.sqlite3`).

| State | Completed (UTC) | Attempted | With taps | Beers found | Errors |
|-------|------------------|-----------|-----------|-------------|--------|
| ME    | 2026-08-13T16:23Z | 66        | 14        | 93          | 0      |
| NH    | 2026-08-13T16:25Z | 72        | 21        | 205         | 0      |
| VT    | 2026-08-13T16:26Z | 49        | 13        | 120         | 0      |
| MA    | 2026-08-13T16:30Z | 134       | 28        | 182         | 0      |
| RI    | 2026-08-13T16:31Z | 30        | 9         | 207         | 0      |
| CT    | 2026-08-13T16:32Z | 63        | 19        | 261         | 0      |
| NY*   | 2026-08-13T16:44Z | 355       | 67        | 565         | 0      |
| NJ*   | 2026-08-13T16:48Z | 96        | 20        | 187         | 0      |
| PA*   | 2026-08-13T16:57Z | 263       | 63        | 480         | 0      |
| DE    | 2026-08-13T16:59Z | 22        | 9         | 35          | 0      |
| MD    | 2026-08-13T17:02Z | 120       | 19        | 156         | 0      |
| DC    | 2026-08-13T17:03Z | 14        | 4         | 27          | 0      |
| VA    | 2026-08-13T17:08Z | 183       | 37        | 322         | 0      |
| WV    | 2026-08-13T17:09Z | 32        | 7         | 53          | 0      |
| NC    | 2026-08-13T17:15Z | 237       | 54        | 425         | 0      |

\* NY, NJ, PA: `--concurrency 15` crashed with `sqlite3.OperationalError: database is locked`
(known SQLite WAL contention issue). Retried successfully at `--concurrency 5`; figures above are from the
successful run. Given the consistent failure at 15 for these larger-brewery-count states, `--concurrency 5`
was used as the default for all subsequent states in this run (still falling back further if needed).
