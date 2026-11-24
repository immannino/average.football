"""Fetch NFL scoreboards from ESPN into data/raw/<season>/<type>-<week>.json.

Finished seasons are cached forever; the current season is re-fetched for any
week that is missing or not fully final. Usage: python pipeline/fetch.py [--from 2002] [--to 2026]
"""
import argparse, json, sys, datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
WEEKS = {2: range(1, 19), 3: range(1, 6)}  # 2=regular season, 3=postseason


def current_season(today=None):
    t = today or datetime.date.today()
    return t.year if t.month >= 8 else t.year - 1


def is_complete(path: Path) -> bool:
    try:
        ev = json.loads(path.read_text())["events"]
    except Exception:
        return False
    return all(e["completed"] for e in ev)


def slim(e):
    """Keep only what the build needs, so the committed cache stays small."""
    c = e["competitions"][0]
    side = {x["homeAway"]: x for x in c["competitors"]}
    return {"id": e["id"], "date": e["date"], "season": e["season"]["year"],
            "completed": bool(c["status"]["type"]["completed"]),
            "home": side["home"]["team"]["abbreviation"], "away": side["away"]["team"]["abbreviation"],
            "home_score": int(side["home"].get("score") or 0), "away_score": int(side["away"].get("score") or 0)}


def fetch_one(job):
    season, stype, week, cur = job
    path = RAW / str(season) / f"{stype}-{week}.json"
    if path.exists() and (season < cur or is_complete(path)):
        return 0
    r = requests.get(URL, params={"dates": season, "seasontype": stype, "week": week}, timeout=30)
    r.raise_for_status()
    d = r.json()
    path.parent.mkdir(parents=True, exist_ok=True)
    keep = {"events": [slim(e) for e in d.get("events", [])]}
    new = json.dumps(keep, separators=(",", ":"), sort_keys=True)
    if path.exists() and path.read_text() == new:
        return 0
    path.write_text(new)
    return 1


TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"


LOGOS = Path(__file__).resolve().parent.parent / "public" / "logos"


def self_host(abbr, src):
    """Download a team logo once into public/logos/ (160px, ~10 KB) and return its site path."""
    out = LOGOS / f"{abbr}.png"
    if not out.exists() and src:
        # the combiner resizes the 500px original to 160px so the site doesn't ship big images
        url = f"https://a.espncdn.com/combiner/i?img={src.split('espncdn.com')[-1]}&w=160&h=160"
        for _ in range(3):
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                LOGOS.mkdir(parents=True, exist_ok=True)
                out.write_bytes(r.content)
                break
            except requests.RequestException:
                continue  # a missing logo falls back to the ESPN URL; the next run retries
    return f"/logos/{abbr}.png" if out.exists() else src


def fetch_teams():
    r = requests.get(TEAMS_URL, timeout=30)
    r.raise_for_status()
    teams = [t["team"] for t in r.json()["sports"][0]["leagues"][0]["teams"]]
    keep = []
    for t in teams:
        src = next((l["href"] for l in t.get("logos", []) if "default" in l.get("rel", [])), None)
        keep.append({"id": t["abbreviation"], "name": t["displayName"], "color": t.get("color"), "logo": self_host(t["abbreviation"], src)})
    (RAW / "teams.json").write_text(json.dumps(sorted(keep, key=lambda x: x["id"]), indent=1))


def main():
    cur = current_season()
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=2002)
    ap.add_argument("--to", dest="end", type=int, default=cur)
    a = ap.parse_args()
    jobs = [(s, t, w, cur) for s in range(a.start, a.end + 1) for t, ws in WEEKS.items() for w in ws]
    with ThreadPoolExecutor(6) as ex:
        changed = sum(ex.map(fetch_one, jobs))
    fetch_teams()
    print(f"fetched/updated {changed} files ({len(jobs)} checked)")


if __name__ == "__main__":
    sys.exit(main())
