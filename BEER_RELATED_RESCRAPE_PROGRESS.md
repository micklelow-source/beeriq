# Targeted re-scrape of "beer_related" breweries (East → West)

Started 2026-08-13. Re-runs discovery + extraction (now with drinks-vocabulary
support, see classifier.py commit cd77db0) for the 2,485 breweries flagged
`beer_related` during the site-classification pass -- i.e. confirmed
beer-related sites that yielded no tap list in the original nationwide sweep.
Targets only this flagged subset per state, not every brewery.

| State | Completed (UTC) | Targeted | Now with taps | Beers found | Errors |
|-------|------------------|----------|----------------|-------------|--------|
| ME    | 2026-08-13T20:02Z | 22       | 0              | 0           | 0      |
| NH    | 2026-08-13T20:03Z | 12       | 0              | 0           | 0      |
| VT    | 2026-08-13T20:04Z | 15       | 1              | 13          | 0      |
| MA    | 2026-08-13T20:06Z | 41       | 2              | 12          | 0      |
| RI    | 2026-08-13T20:06Z | 6        | 0              | 0           | 0      |
| CT    | 2026-08-13T20:08Z | 21       | 1              | 4           | 0      |
| NY    | 2026-08-13T20:10Z | 122      | 2              | 10          | 0      |
| NJ    | 2026-08-13T20:12Z | 44       | 3              | 6           | 0      |
| PA    | 2026-08-13T20:15Z | 88       | 5              | 64          | 0      |
| DE    | 2026-08-13T20:16Z | 6        | 0              | 0           | 0      |
