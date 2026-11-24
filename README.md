# average.football

Tracking the NFL's gauntlets: which teams are chasing a group of teams (birds, cats, mythical creatures, guys, ...)
and have beaten every one of them in a single season. Live at https://www.average.football

## How it works
- `pipeline/fetch.py` pulls scoreboards (2002 on) from ESPN into `data/raw/` (small, committed cache) and team logos/names.
- `pipeline/build.py` loads them into DuckDB (`data/af.duckdb`, rebuildable), computes gauntlet results in SQL and exports
  CSV, JSON and a SQLite file to `public/data/`. `pipeline/check.py` sanity-checks the output.
- The Vue 3 + Vite site in `src/` reads those static files. Gauntlet definitions live in `data/gauntlets.json`.
- `.github/workflows/update.yml` refreshes the data on a schedule, then builds and deploys to GitHub Pages.

## Ribbons, digest and share cards
- Every gauntlet has a silly ribbon name (`ribbon` in `data/gauntlets.json`). Tiers come from how rarely qualifying teams complete it:
  legendary <5%, gold <25%, silver <40%, bronze otherwise, unclaimed if nobody has since 2002 (`src/stats.js`).
- `build.py` diffs the live season against `data/state/status.json` and writes `public/data/digest.json` / `digest.md`
  (completed, one win away, failed). The scheduled job saves the state (`AF_SAVE_STATE=1`); local runs never do.
- `npm run cards` renders 1080x1350 share images to `out/cards/` (needs Chrome; set `CHROME=` to override) for Instagram.
  Caption text is in `digest.md`.

## Develop
```
uv sync && uv run python pipeline/fetch.py && uv run python pipeline/build.py && uv run python pipeline/check.py
npm install && npm run dev
npm run sky   # regenerate the pixel sky texture
```
Rules: a gauntlet is complete when a team beats every other team in the group in the same season (regular season or
playoffs; ties don't count). A team only qualifies if its schedule includes all of them.
