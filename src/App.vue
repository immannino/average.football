<script setup>
import { ref, computed, onMounted, onUnmounted, provide } from 'vue'
import RibbonBadge from './RibbonBadge.vue'
import { tierOf } from './stats.js'
import TeamView from './TeamView.vue'
import GauntletView from './GauntletView.vue'
import GauntletTable from './GauntletTable.vue'
import TeamChip from './TeamChip.vue'
import OpponentRows from './OpponentRows.vue'
import { loadGames } from './games.js'
import CardView from './CardView.vue'
import DataPage from './DataPage.vue'
import GauntletList from './GauntletList.vue'
import TeamList from './TeamList.vue'
import { teamName } from './teamNames.js'

const gauntlets = ref([]), teamSeasons = ref([]), results = ref([]), seasons = ref([]), teams = ref([]), loading = ref(true)
const season = ref(null)
const logos = ref({})
const games = ref(null)
provide('logos', logos)

const parse = () => {
  const [k, v] = location.hash.slice(1).split('=')
  if (k === 'team' && v) return { view: 'team', id: v }
  if (k === 'card') return { view: 'card', id: v }
  if (k === 'data') return { view: 'data', id: '' }
  if (k === 'teams') return { view: 'teams', id: '' }
  if (k === 'gauntlet' && v) return { view: 'gauntlet', id: v }
  if (k === 'gauntlets') return { view: 'gauntlets', id: '' }
  return { view: 'overview', id: '' }
}
const route = ref(parse())
const onHash = () => (route.value = parse())
onMounted(async () => {
  window.addEventListener('hashchange', onHash)
  loadGames().then((g) => (games.value = g))
  const get = (n) => fetch(`${import.meta.env.BASE_URL}data/${n}.json`).then((r) => r.json())
  const [g, r, s] = await Promise.all([get('gauntlets'), get('gauntlet_results'), get('team_seasons')])
  get('teams').then((t) => (logos.value = Object.fromEntries(t.map((x) => [x.id, x.logo])))).catch(() => {})
  gauntlets.value = g
  const ts = new Map(s.map((x) => [`${x.season}-${x.team}`, x]))
  r.forEach((x) => (x.ts = ts.get(`${x.season}-${x.team}`)))
  results.value = r
  teamSeasons.value = s
  teams.value = [...new Set(s.map((x) => x.team))].sort()
  seasons.value = [...new Set(s.map((x) => x.season))].sort((a, b) => b - a)
  season.value = seasons.value[0]
  loading.value = false
})
onUnmounted(() => window.removeEventListener('hashchange', onHash))

const current = computed(() => season.value === seasons.value[0])
const cards = computed(() =>
  gauntlets.value.map((g) => {
    const rows = results.value.filter((r) => r.gauntlet === g.id && r.season === season.value)
    const done = rows.filter((r) => r.status === 'complete')
    const alive = rows.filter((r) => r.status === 'in-progress').sort((a, b) => b.beaten_count / b.required - a.beaten_count / a.required)
    const failed = rows.filter((r) => r.status === 'failed')
    const reason = !rows.length ? `No team plays all ${g.teams.length} of these teams` : `${failed.length} qualifying team${failed.length > 1 ? 's' : ''}, all failed`
    const h = rarity.value[g.id]
    return { ...g, rows, done, alive, failed, reason, h, on: done.length > 0 || alive.length > 0 }
  }),
)
// Rarity = how rarely qualifying teams have completed it in finished seasons (rank 1 = rarest).
const rarity = computed(() => {
  const past = results.value.filter((r) => r.season !== seasons.value[0])
  const out = {}
  gauntlets.value.forEach((g) => {
    const rs = past.filter((r) => r.gauntlet === g.id)
    const done = rs.filter((r) => r.complete).length
    out[g.id] = { done, attempts: rs.length, rate: rs.length ? done / rs.length : 0, size: g.teams.length }
  })
  const order = Object.keys(out).sort((a, b) => out[a].rate - out[b].rate || out[b].size - out[a].size)
  order.forEach((id, i) => (out[id].rank = i + 1))
  return out
})
provide('rarity', rarity)
const onBoard = computed(() => cards.value.filter((c) => c.on).sort((a, b) => a.h.rank - b.h.rank))
const watchTeams = computed(() => new Set(onBoard.value.flatMap((c) => c.alive.map((r) => r.team))).size)
const mode = ref((() => { try { return new URLSearchParams(location.search).get('mode') || localStorage.getItem('af-mode') || 'cards' } catch { return 'cards' } })())
const setMode = (m) => { mode.value = m; try { localStorage.setItem('af-mode', m) } catch {} }
const tableRows = computed(() =>
  results.value.filter((r) => r.season === season.value).map((r) => ({
    ...r, name: gauntlets.value.find((g) => g.id === r.gauntlet).name, rank: rarity.value[r.gauntlet].rank })),
)
const dead = computed(() => cards.value.filter((c) => !c.on))
const rec = (t) => (t ? `${t.wins}-${t.losses}${t.ties ? '-' + t.ties : ''}` : '')
const split = (s) => (s ? s.split(',') : [])
</script>

<template>
  <div v-if="route.view === 'card'">
    <CardView v-if="!loading" :id="route.id" :gauntlets="gauntlets" :results="results" :seasons="seasons" />
  </div>
  <div v-else class="app-shell">
  <header class="app-header">
    <a class="app-brand" href="#"><img src="/favicon.svg" alt="" class="logo" width="24" height="24" />average<span>.football</span></a>
    <a class="nav-chip" href="#" :class="{ on: route.view === 'overview' }">Watch</a>
    <a class="nav-chip" href="#gauntlets" :class="{ on: route.view.startsWith('gauntlet') }">Gauntlets</a>
    <a class="nav-chip" href="#teams" :class="{ on: route.view.startsWith('team') }">Teams</a>
    <a class="nav-chip" href="#data" :class="{ on: route.view === 'data' }">Data</a>
    <label class="chip-label" v-if="route.view === 'overview' && !loading">Season
      <select v-model="season"><option v-for="s in seasons" :key="s" :value="s">{{ s }}{{ s === seasons[0] ? ' (live)' : '' }}</option></select>
    </label>
  </header>

  <main v-if="loading" class="app-main"><p class="loading">Loading…</p></main>
  <main v-else-if="route.view === 'data'" class="app-main wide">
    <h1 class="page-title">Data</h1>
    <p class="page-sub">Everything on this site, as plain files. Rebuilt whenever games finish.</p>
    <DataPage />
  </main>
  <main v-else-if="route.view === 'teams'" class="app-main wide">
    <h1 class="page-title">All teams</h1>
    <p class="page-sub">Pick a team to see every gauntlet it qualified for.</p>
    <TeamList :teams="teams" :results="results" :seasons="seasons" :team-seasons="teamSeasons" />
  </main>
  <main v-else-if="route.view === 'team'" class="app-main wide">
    <p class="crumb"><a href="#teams">← All teams</a></p>
    <h1 class="page-title"><img v-if="logos[route.id]" :src="logos[route.id]" alt="" class="hero-logo" />{{ teamName(route.id) }}</h1>
    <TeamView :gauntlets="gauntlets" :results="results" :seasons="seasons" :teams="teams" :initial="route.id" />
  </main>
  <main v-else-if="route.view === 'gauntlets'" class="app-main wide">
    <h1 class="page-title">All gauntlets</h1>
    <p class="page-sub">Pick a gauntlet to see every team that ever completed it.</p>
    <GauntletList :gauntlets="gauntlets" :results="results" :seasons="seasons" :rarity="rarity" />
  </main>
  <main v-else-if="route.view === 'gauntlet'" class="app-main wide">
    <p class="crumb"><a href="#gauntlets">← All gauntlets</a></p>
    <h1 class="page-title">{{ gauntlets.find((g) => g.id === route.id)?.name }} gauntlet</h1>
    <GauntletView :gauntlets="gauntlets" :results="results" :seasons="seasons" :initial="route.id" />
  </main>
  <main v-else class="app-main">
    <h1 class="page-title page-title-hero">{{ current ? 'Which teams are chasing an NFL gauntlet?' : 'Gauntlets completed in ' + season }}</h1>
    <section class="window full" data-title="WHAT IS A GAUNTLET?">
      <p>A gauntlet is a group of teams with something in common: birds, cats, mythical creatures, and guys. A team <b>completes</b> it by
        <b>beating every team in the group in the same season</b>. It almost never happens, so we watch who is still in the hunt.</p>
      <p class="legend"><span class="dot b-done"></span>complete <span class="dot b-live"></span>on watch (still possible)
        <span class="dot b-fail"></span>failed or impossible</p>
    </section>

    <h2 class="sec">{{ current ? `Gauntlet Watch · ${season}` : `${onBoard.length} gauntlets` }}
      <small v-if="current">{{ watchTeams }} team{{ watchTeams === 1 ? '' : 's' }} still chasing, {{ onBoard.length }} gauntlets in play, rarest first</small></h2>
    <div class="modes full">
      <button :class="{ on: mode === 'cards' }" @click="setMode('cards')">Cards</button>
      <button :class="{ on: mode === 'table' }" @click="setMode('table')">Table</button>
    </div>
    <GauntletTable v-if="mode === 'table'" :rows="tableRows" :current="current" />
    <p v-if="mode === 'cards' && !onBoard.length" class="muted full">Nothing completed in {{ season }}.</p>
    <section v-for="c in (mode === 'cards' ? onBoard : [])" :key="c.id" class="window" :class="c.done.length ? 'done' : 'live'"
      :data-title="`${c.name.toUpperCase()} GAUNTLET · #${c.h.rank} OF ${gauntlets.length} RAREST`">
      <h2>
        <a :href="`#gauntlet=${c.id}`"><RibbonBadge :tier="tierOf(c.h)" :size="18" /> {{ c.name }}</a>
        <span class="badge" :class="c.done.length ? 'b-done' : 'b-live'">{{ c.done.length ? 'COMPLETE' : 'ON WATCH' }}</span>
      </h2>
      <p class="stat">Ribbon: <b>{{ c.ribbon }}</b>. Done {{ c.h.done }} time{{ c.h.done === 1 ? '' : 's' }} in {{ c.h.attempts }} attempts since 2002.</p>
      <p class="teams">Must beat all {{ c.teams.length }}:
        <TeamChip v-for="t in c.teams" :key="t" :team="t" /></p>
      <ul v-if="c.done.length">
        <li v-for="r in c.done" :key="r.team">
          ✓ <TeamChip :team="r.team" bold /> completed it, {{ rec(r.ts) }}
          <span v-if="r.ts?.champion">🏆</span><em v-if="r.is_member">member</em>
        </li>
      </ul>
      <template v-if="c.alive.length">
        <p class="sub">{{ current ? 'Still chasing it' : 'Alive' }} ({{ c.alive.length }})</p>
        <ul>
          <li v-for="r in c.alive" :key="r.team">
            <TeamChip :team="r.team" bold /> {{ r.beaten_count }}/{{ r.required }}
            <span class="bar"><i :style="{ width: (100 * r.beaten_count) / r.required + '%' }"></i></span>
            <OpponentRows v-if="games" :team="r.team" :opps="c.teams" :games="games" :season="season" compact />
            <span v-else class="needs">still needs {{ split(r.missing).join(', ') }}</span>
          </li>
        </ul>
      </template>
      <p v-if="c.failed.length" class="muted small">{{ c.failed.length }} other team{{ c.failed.length > 1 ? 's' : '' }} failed:
        <template v-for="(r, i) in c.failed" :key="r.team"><a :href="`#team=${r.team}`">{{ r.team }}</a>{{ i < c.failed.length - 1 ? ', ' : '' }}</template></p>
    </section>

    <h2 class="sec">{{ current ? 'Out of reach this season' : 'Nobody completed' }} <small>{{ dead.length }} gauntlets</small></h2>
    <section class="card full deadlist">
      <ul>
        <li v-for="c in dead" :key="c.id"><a :href="`#gauntlet=${c.id}`"><b>{{ c.name }}</b></a> <span>{{ c.reason }}</span></li>
        <li v-if="!dead.length" class="muted">None. Every gauntlet is on the board.</li>
      </ul>
    </section>
  </main>
  </div>
</template>
