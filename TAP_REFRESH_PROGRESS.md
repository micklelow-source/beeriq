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
| SC    | 2026-08-13T17:17Z | 60        | 13        | 173         | 0      |
| GA    | 2026-08-13T17:20Z | 72        | 13        | 99          | 0      |
| FL    | 2026-08-13T18:37Z | 230       | 44        | 369         | 0      |
| AL    | 2026-08-13T18:38Z | 34        | 12        | 82          | 0      |
| MS    | 2026-08-13T18:39Z | 15        | 3         | 38          | 0      |
| TN    | 2026-08-13T18:42Z | 88        | 21        | 152         | 0      |
| KY    | 2026-08-13T18:43Z | 43        | 3         | 46          | 0      |
| LA    | 2026-08-13T18:44Z | 32        | 9         | 83          | 0      |
| AR    | 2026-08-13T18:46Z | 34        | 4         | 13          | 0      |
| OK    | 2026-08-13T18:47Z | 36        | 10        | 75          | 0      |
| TX    | 2026-08-13T18:54Z | 262       | 51        | 468         | 0      |
| OH    | 2026-08-13T18:59Z | 221       | 50        | 514         | 0      |
| MI    | 2026-08-13T19:06Z | 282       | 51        | 529         | 0      |
| IN    | 2026-08-13T19:08Z | 119       | 11        | 97          | 0      |
| IL    | 2026-08-13T19:13Z | 209       | 41        | 342         | 0      |
| WI    | 2026-08-13T19:17Z | 182       | 33        | 209         | 0      |
| MN    | 2026-08-13T19:21Z | 152       | 29        | 212         | 0      |
| IA    | 2026-08-13T19:22Z | 76        | 13        | 111         | 0      |
| MO    | 2026-08-13T19:26Z | 121       | 25        | 213         | 0      |
| KS    | 2026-08-13T19:27Z | 33        | 4         | 41          | 0      |
| NE    | 2026-08-13T19:28Z | 55        | 12        | 94          | 0      |
| ND    | 2026-08-13T19:29Z | 20        | 2         | 8           | 0      |
| SD    | 2026-08-13T19:31Z | 37        | 6         | 51          | 0      |
| MT    | 2026-08-13T19:33Z | 72        | 19        | 105         | 0      |
| WY    | 2026-08-13T19:35Z | 42        | 9         | 73          | 0      |
| CO    | 2026-08-13T19:44Z | 355       | 80        | 824         | 0      |
| NM    | 2026-08-13T19:46Z | 66        | 15        | 101         | 0      |
| UT    | 2026-08-13T19:47Z | 34        | 12        | 130         | 0      |
| ID    | 2026-08-13T19:49Z | 59        | 12        | 70          | 0      |
| AZ    | 2026-08-13T19:53Z | 96        | 15        | 95          | 0      |

\* NY, NJ, PA: `--concurrency 15` crashed with `sqlite3.OperationalError: database is locked`
(known SQLite WAL contention issue). Retried successfully at `--concurrency 5`; figures above are from the
successful run. Given the consistent failure at 15 for these larger-brewery-count states, `--concurrency 5`
was used as the default for all subsequent states in this run (still falling back further if needed).
