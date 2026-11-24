"""Load cached raw JSON into DuckDB, compute gauntlet results, export CSV+JSON to public/data."""
import json
import os
import sqlite3
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT, DB = ROOT / "data" / "raw", ROOT / "public" / "data", ROOT / "data" / "af.duckdb"

# historical ESPN abbreviations -> current franchise id
ALIAS = {"STL": "LAR", "SD": "LAC", "OAK": "LV", "WAS": "WSH", "LA": "LAR"}
SKIP = {"AFC", "NFC", "NPR", "RIC", "CAN", "IRV", "SAN", "TEAM", "TBD"}  # Pro Bowl etc.


def load_games():
    rows = {}
    for f in sorted(RAW.glob("*/*.json")):
        stype = "reg" if f.name.startswith("2-") else "post"
        for e in json.loads(f.read_text())["events"]:
            h, a = ALIAS.get(e["home"], e["home"]), ALIAS.get(e["away"], e["away"])
            if h in SKIP or a in SKIP:
                continue
            done = e["completed"]
            rows[e["id"]] = (e["id"], e["season"], stype, e["date"], h, a,
                             e["home_score"] if done else None, e["away_score"] if done else None, done)
    out = list(rows.values())
    # A game still unplayed in a past season was postponed (2014 BUF-NYJ snow, 2017 MIA-TB hurricane;
    # both replayed under another id) or cancelled (2022 CIN-BUF). It is not a game that "still needs
    # playing", so keeping it would show a stale "next up" and count as a scheduled opponent.
    latest = max(r[1] for r in out)
    return [r for r in out if r[8] or r[1] == latest]


def export_sqlite(con):
    """Same data as the CSV/JSON exports, as one portable SQLite file for people who want to query it."""
    path = OUT / "af.sqlite"
    path.unlink(missing_ok=True)
    db = sqlite3.connect(path)
    tables = {"games": "SELECT * FROM games", "team_seasons": "SELECT * FROM team_seasons",
              "gauntlet_results": "SELECT * FROM gauntlet_results WHERE qualifies",
              "gauntlets": "SELECT * FROM gauntlets", "gauntlet_teams": "SELECT * FROM gauntlet_teams"}
    for name, q in tables.items():
        cur = con.execute(q)
        cols = [d[0] for d in cur.description]
        db.execute(f"CREATE TABLE {name} ({', '.join(cols)})")
        db.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})", cur.fetchall())
    teams = RAW / "teams.json"
    if teams.exists():
        db.execute("CREATE TABLE teams (id, name, color, logo)")
        db.executemany("INSERT INTO teams VALUES (?,?,?,?)", [(t["id"], t["name"], t["color"], t["logo"]) for t in json.loads(teams.read_text())])
    db.execute("""CREATE VIEW completions AS SELECT r.season, r.gauntlet, r.team, r.is_member, s.wins, s.losses, s.ties,
                  s.playoff_games, s.playoff_wins, s.champion FROM gauntlet_results r JOIN team_seasons s USING (season, team)
                  WHERE r.complete""")
    db.commit()
    db.close()


STATE = ROOT / "data" / "state" / "status.json"


def write_digest(con, gauntlets):
    """Diff the live season against the last saved state and write what changed (digest.json / digest.md).

    State is only saved when AF_SAVE_STATE=1 (the scheduled job), so local runs never swallow events.
    With no saved state yet, every live status is reported as a baseline.
    """
    season = con.execute("SELECT max(season) FROM games").fetchone()[0]
    info = {x["id"]: x for x in gauntlets}
    teams = {t["id"]: t["name"] for t in json.loads((RAW / "teams.json").read_text())} if (RAW / "teams.json").exists() else {}
    rows = con.execute("""SELECT r.gauntlet, r.team, r.status, r.beaten_count, r.required, r.missing, r.lost_to,
                          s.wins, s.losses, s.ties FROM gauntlet_results r JOIN team_seasons s USING (season, team)
                          WHERE r.qualifies AND r.season = ?""", [season]).fetchall()
    now = {f"{g}|{t}": {"status": st, "beaten": b, "required": rq} for g, t, st, b, rq, *_ in rows}
    prev = json.loads(STATE.read_text()) if STATE.exists() else None
    last = con.execute("SELECT max(date) FROM games WHERE completed").fetchone()[0][:10]

    def next_game(team, opps):
        for o in opps:
            r = con.execute("""SELECT date, home FROM games WHERE NOT completed AND season=? AND
                               ((home=? AND away=?) OR (home=? AND away=?)) ORDER BY date LIMIT 1""", [season, team, o, o, team]).fetchone()
            if r:
                return {"opp": o, "date": r[0][:10], "home": r[1] == team}
        return None

    events = []
    for g, t, st, b, rq, missing, lost_to, w, l, ti in rows:
        p = (prev or {}).get(f"{g}|{t}")
        one_away = st == "in-progress" and b == rq - 1
        was_one_away = p and p["status"] == "in-progress" and p["beaten"] == p["required"] - 1
        kind = None
        if st == "complete" and not (p and p["status"] == "complete"):
            kind = "complete"
        elif st == "failed" and not (p and p["status"] == "failed"):
            kind = "failed"
        elif one_away and not was_one_away:
            kind = "one_away"
        if not kind:
            continue
        miss = [m for m in (missing or "").split(",") if m]
        events.append({"kind": kind, "season": season, "gauntlet": g, "gauntlet_name": info[g]["name"], "ribbon": info[g]["ribbon"],
                       "team": t, "team_name": teams.get(t, t), "record": f"{w}-{l}" + (f"-{ti}" if ti else ""),
                       "beaten": b, "required": rq, "missing": miss, "lost_to": [m for m in (lost_to or "").split(",") if m],
                       "next": next_game(t, miss) if kind == "one_away" else None})
    order = {"complete": 0, "one_away": 1, "failed": 2}
    events.sort(key=lambda e: (order[e["kind"]], e["gauntlet"], e["team"]))

    out = OUT / "digest.json"
    if events or not out.exists():
        out.write_text(json.dumps({"season": season, "as_of": last, "baseline": prev is None, "events": events}, indent=1))
        lines = [f"# Gauntlet digest, {season} season (as of {last})" + (" [baseline]" if prev is None else ""), ""]
        for e in events:
            if e["kind"] == "complete":
                lines.append(f"- 🎀 **{e['team_name']}** completed the **{e['gauntlet_name']}** gauntlet ({e['ribbon']}), {e['record']}.")
            elif e["kind"] == "one_away":
                n = e["next"]
                tail = f" Next: {'vs' if n['home'] else '@'} {n['opp']} on {n['date']}." if n else ""
                lines.append(f"- 👀 **{e['team_name']}** is one win from the **{e['gauntlet_name']}** gauntlet (needs {', '.join(e['missing'])}).{tail}")
            else:
                lines.append(f"- ✗ **{e['team_name']}** failed the **{e['gauntlet_name']}** gauntlet (missed {', '.join(e['lost_to'])}).")
        (OUT / "digest.md").write_text("\n".join(lines) + "\n")
    print(f"digest: {len(events)} events" + (" (baseline)" if prev is None else ""))
    if os.environ.get("AF_SAVE_STATE") == "1":
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(now, indent=0, sort_keys=True))


def main():
    DB.unlink(missing_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("""CREATE TABLE games(id VARCHAR PRIMARY KEY, season INT, type VARCHAR, date VARCHAR,
                   home VARCHAR, away VARCHAR, home_score INT, away_score INT, completed BOOLEAN)""")
    con.executemany("INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?)", load_games())

    g = json.loads((ROOT / "data" / "gauntlets.json").read_text())
    con.execute("CREATE TABLE gauntlets(id VARCHAR, name VARCHAR)")
    con.execute("CREATE TABLE gauntlet_teams(gauntlet VARCHAR, team VARCHAR)")
    con.executemany("INSERT INTO gauntlets VALUES (?,?)", [(x["id"], x["name"]) for x in g])
    con.executemany("INSERT INTO gauntlet_teams VALUES (?,?)", [(x["id"], t) for x in g for t in x["teams"]])

    # one row per team per game
    con.execute("""CREATE VIEW team_games AS
      SELECT season, type, date, home AS team, away AS opp, home_score AS pf, away_score AS pa, completed FROM games
      UNION ALL SELECT season, type, date, away, home, away_score, home_score, completed FROM games""")

    con.execute("""CREATE TABLE team_seasons AS
      WITH last_game AS (SELECT season, max(date) AS d FROM games WHERE type='post' GROUP BY season)
      SELECT t.season, t.team,
        count(*) FILTER (WHERE type='reg' AND pf>pa) AS wins,
        count(*) FILTER (WHERE type='reg' AND pf<pa) AS losses,
        count(*) FILTER (WHERE type='reg' AND pf=pa) AS ties,
        count(*) FILTER (WHERE type='post') AS playoff_games,
        count(*) FILTER (WHERE type='post' AND pf>pa) AS playoff_wins,
        bool_or(type='post' AND pf>pa AND t.date=l.d) AS champion
      FROM team_games t LEFT JOIN last_game l USING (season) WHERE t.completed GROUP BY t.season, t.team""")

    # every team x gauntlet x season; required = members minus self.
    # qualifies: the team plays (or is scheduled to play) every required opponent.
    # dead: a missing opponent with no win and no game left -> failed.
    con.execute("""CREATE TABLE gauntlet_results AS
      WITH req AS (
        SELECT ts.season, ts.team, gt.gauntlet, gt.team AS opp
        FROM team_seasons ts JOIN gauntlet_teams gt ON gt.team <> ts.team),
      f AS (SELECT season, team, opp,
              bool_or(completed AND pf>pa) AS won,
              bool_or(NOT completed) AS to_play,
              count(*) AS games FROM team_games GROUP BY ALL),
      j AS (SELECT r.season, r.team, r.gauntlet, r.opp,
              coalesce(f.games,0)>0 AS faced, coalesce(f.won,false) AS won, coalesce(f.to_play,false) AS to_play
            FROM req r LEFT JOIN f ON f.season=r.season AND f.team=r.team AND f.opp=r.opp),
      agg AS (SELECT season, team, gauntlet,
        count(*) AS required,
        count(*) FILTER (WHERE won) AS beaten_count,
        bool_and(faced) AS qualifies,
        string_agg(opp, ',') FILTER (WHERE won) AS beaten,
        string_agg(opp, ',') FILTER (WHERE NOT won) AS missing,
        string_agg(opp, ',') FILTER (WHERE NOT won AND to_play) AS remaining,
        string_agg(opp, ',') FILTER (WHERE NOT won AND faced AND NOT to_play) AS lost_to
      FROM j GROUP BY season, team, gauntlet)
      SELECT a.*,
        EXISTS (SELECT 1 FROM gauntlet_teams x WHERE x.gauntlet=a.gauntlet AND x.team=a.team) AS is_member,
        beaten_count = required AS complete,
        CASE WHEN beaten_count = required THEN 'complete'
             WHEN lost_to IS NOT NULL THEN 'failed' ELSE 'in-progress' END AS status
      FROM agg a""")

    OUT.mkdir(parents=True, exist_ok=True)
    for name, q in {
        "games": "SELECT * FROM games ORDER BY date",
        "team_seasons": "SELECT * FROM team_seasons ORDER BY season, team",
        "gauntlet_results": "SELECT * FROM gauntlet_results WHERE qualifies ORDER BY season, gauntlet, team",
        "completions": """SELECT r.season, r.gauntlet, r.team, r.is_member, s.wins, s.losses, s.ties,
                          s.playoff_games, s.playoff_wins, s.champion
                          FROM gauntlet_results r JOIN team_seasons s USING (season, team)
                          WHERE r.complete AND r.qualifies ORDER BY r.season, r.gauntlet, r.team""",
    }.items():
        con.execute(f"COPY ({q}) TO '{OUT / (name + '.csv')}' (HEADER)")
        rows = con.execute(q).fetchall()
        cols = [d[0] for d in con.description]
        (OUT / f"{name}.json").write_text(json.dumps([dict(zip(cols, r)) for r in rows], separators=(",", ":")))
    teams = RAW / "teams.json"
    if teams.exists():
        (OUT / "teams.json").write_text(teams.read_text())
    (OUT / "gauntlets.json").write_text((ROOT / "data" / "gauntlets.json").read_text())
    export_sqlite(con)
    write_digest(con, g)
    print("games:", con.execute("SELECT count(*) FROM games").fetchone()[0],
          "completions:", con.execute("SELECT count(*) FROM gauntlet_results WHERE complete AND qualifies").fetchone()[0])


if __name__ == "__main__":
    main()
