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
