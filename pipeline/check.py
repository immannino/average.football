"""Sanity checks on the built database. Run after build.py: uv run python pipeline/check.py"""
from pathlib import Path
import duckdb

con = duckdb.connect(str(Path(__file__).resolve().parent.parent / "data" / "af.duckdb"), read_only=True)
q = lambda sql: con.execute(sql).fetchall()
fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


check("32 teams every finished season", not q("""SELECT season FROM (SELECT season, count(DISTINCT team) n FROM team_seasons GROUP BY season)
                                               WHERE n <> 32 AND season < (SELECT max(season) FROM games)"""))
check("no game vs itself", not q("SELECT 1 FROM games WHERE home = away"))
check("completed games have scores", not q("SELECT 1 FROM games WHERE completed AND (home_score IS NULL OR away_score IS NULL)"))
check("complete means beaten == required", not q("SELECT 1 FROM gauntlet_results WHERE complete AND beaten_count <> required"))
check("status complete iff complete", not q("SELECT 1 FROM gauntlet_results WHERE complete <> (status = 'complete')"))
check("failed rows name who was missed", not q("SELECT 1 FROM gauntlet_results WHERE status = 'failed' AND lost_to IS NULL"))
check("in-progress rows have nobody lost", not q("SELECT 1 FROM gauntlet_results WHERE status = 'in-progress' AND lost_to IS NOT NULL"))
check("past seasons never in-progress", not q("SELECT 1 FROM gauntlet_results WHERE qualifies AND status = 'in-progress' AND season < (SELECT max(season) FROM games)"))
check("no unplayed games in past seasons", not q("SELECT 1 FROM games WHERE NOT completed AND season < (SELECT max(season) FROM games)"))
check("a team never needs itself", not q("SELECT 1 FROM gauntlet_results WHERE list_contains(string_split(coalesce(beaten,'') || ',' || coalesce(missing,''), ','), team)"))
check("known: nobody has completed Bird since 2002", q("SELECT count(*) FROM gauntlet_results WHERE gauntlet='bird' AND complete")[0][0] == 0)
check("known: 2002 season has 256 regular-season games", q("SELECT count(*) FROM games WHERE season=2002 AND type='reg'")[0][0] == 256)
raise SystemExit(1 if fails else 0)
