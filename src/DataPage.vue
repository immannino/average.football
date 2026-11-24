<script setup>
const base = import.meta.env.BASE_URL + 'data/'
const files = [
  { id: 'af', title: 'SQLite database', what: 'All of the tables below in one file, plus a completions view. Open it with sqlite3, DB Browser, or any SQLite library.',
    cols: 'tables: games, team_seasons, gauntlet_results, gauntlets, gauntlet_teams, teams · view: completions', sqlite: true },
  { id: 'completions', title: 'Completions', what: 'Every completed gauntlet: one row per team per gauntlet per season, with the team\'s record and playoff result.',
    cols: 'season, gauntlet, team, is_member, wins, losses, ties, playoff_games, playoff_wins, champion' },
  { id: 'gauntlet_results', title: 'Gauntlet results', what: 'Every team-season that played (or is scheduled to play) every team in a gauntlet, with its progress and status.',
    cols: 'season, team, gauntlet, required, beaten_count, qualifies, beaten, missing, remaining, lost_to, is_member, complete, status (complete | in-progress | failed)' },
  { id: 'team_seasons', title: 'Team seasons', what: 'Regular-season record, playoff games and wins, and whether the team won the title, for each team and season.',
    cols: 'season, team, wins, losses, ties, playoff_games, playoff_wins, champion' },
  { id: 'games', title: 'Games', what: 'Every NFL game since 2002 (regular season and playoffs), including scheduled games not yet played.',
    cols: 'id, season, type (reg | post), date, home, away, home_score, away_score, completed' },
  { id: 'gauntlets', title: 'Gauntlet definitions', what: 'Which teams belong to each gauntlet. JSON only.', cols: 'id, name, teams[]', jsonOnly: true },
  { id: 'teams', title: 'Teams', what: 'Team ids (ESPN abbreviations), names, colors and logo URLs. JSON only.', cols: 'id, name, color, logo', jsonOnly: true },
]
</script>

<template>
  <section class="window" data-title="DOWNLOADS">
    <p class="intro">Free to use. A gauntlet is complete when a team beats every other team in the group in one season (regular season or playoffs, ties don't count).
      Team ids are ESPN abbreviations; relocated franchises use their current id (STL is LAR, SD is LAC, OAK is LV).</p>
    <article v-for="f in files" :key="f.id" class="file">
      <div class="head">
        <h2>{{ f.title }}</h2>
        <span class="dl">
          <a v-if="f.sqlite" class="chip" :href="`${base}af.sqlite`" download>SQLite</a>
          <template v-else>
            <a v-if="!f.jsonOnly" class="chip" :href="`${base}${f.id}.csv`" download>CSV</a>
            <a class="chip" :href="`${base}${f.id}.json`" download>JSON</a>
          </template>
        </span>
      </div>
      <p>{{ f.what }}</p>
      <p class="cols"><code>{{ f.cols }}</code></p>
    </article>
  </section>
</template>

<style scoped>
.intro { font-size:.9rem; margin:0 0 12px }
.file { background:#fff; border:1px solid var(--line); padding:10px 14px; margin-bottom:10px }
.head { display:flex; justify-content:space-between; align-items:center; gap:8px } h2 { margin:0; font-size:1.05rem; font-weight:500 }
.dl .chip { padding:.1rem .6rem; margin-left:6px }
p { margin:4px 0; font-size:.88rem } .cols { color:var(--muted) } code { font-family:var(--font-mono); font-size:.76rem; word-break:break-word }
</style>
