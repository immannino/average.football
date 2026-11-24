<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import RibbonBadge from './RibbonBadge.vue'
import { tierOf, tierNote } from './stats.js'
import { teamName } from './teamNames.js'
import OpponentRows from './OpponentRows.vue'
import { loadGames, teamGames, opponentRows } from './games.js'

const props = defineProps({ gauntlets: Array, results: Array, seasons: Array, teams: Array, initial: String })
const team = ref(props.initial && props.teams.includes(props.initial) ? props.initial : props.teams[0])
const season = ref(props.seasons[0])
watch(() => props.initial, (v) => v && props.teams.includes(v) && (team.value = v))
watch(team, (t) => (location.hash = `#team=${t}`))

const rarity = inject('rarity', ref({}))
const shelf = computed(() => {
  const mine = props.results.filter((r) => r.team === team.value && r.complete)
  const earned = [], open = []
  props.gauntlets.forEach((g) => {
    const years = mine.filter((r) => r.gauntlet === g.id).map((r) => r.season).sort((a, b) => a - b)
    const tier = tierOf(rarity.value[g.id])
    ;(years.length ? earned : open).push({ g, years, tier })
  })
  return { earned: earned.sort((a, b) => b.years.length - a.years.length), open }
})
const games = ref(null)
onMounted(async () => (games.value = await loadGames()))

const rows = computed(() => {
  const mine = props.results.filter((r) => r.team === team.value)
  return mine
    .filter((r) => r.season === season.value)
    .map((r) => {
      const g = props.gauntlets.find((g) => g.id === r.gauntlet)
      const x = { r, g, status: r.status, years: mine.filter((m) => m.gauntlet === r.gauntlet && m.complete).map((m) => m.season).sort() }
      x.opps = x.g.teams.filter((t) => t !== team.value)
      x.next = opponentRows(teamGames(games.value, team.value, season.value), x.opps).find((o) => o.state === 'next')?.next
      return x
    })
    .sort((a, b) => order[a.status] - order[b.status] || b.r.beaten_count / b.r.required - a.r.beaten_count / a.r.required)
})
const order = { complete: 0, 'in-progress': 1, failed: 2 }
const label = { complete: 'Complete', 'in-progress': 'In progress', failed: 'Failed' }
</script>

<template>
  <div class="tv">
    <div class="pick">
      <label class="chip-label inline">Team <select v-model="team"><option v-for="t in teams" :key="t" :value="t">{{ teamName(t) }}</option></select></label>
      <label class="chip-label inline">Season <select v-model="season"><option v-for="s in seasons" :key="s">{{ s }}</option></select></label>
    </div>
    <section class="shelf window" :data-title="`${teamName(team).toUpperCase()} · RIBBONS ${shelf.earned.length}/${gauntlets.length}`">
      <div class="earned">
        <div v-for="x in shelf.earned" :key="x.g.id" class="rib" :title="tierNote">
          <RibbonBadge :tier="x.tier" :size="32" />
          <div>
            <b>{{ x.g.ribbon }}</b> <span v-if="x.years.length > 1" class="x">×{{ x.years.length }}</span>
            <small>{{ x.g.name }} · {{ x.years.join(', ') }}</small>
          </div>
        </div>
        <p v-if="!shelf.earned.length" class="n">No ribbons yet. {{ teamName(team) }} hasn't completed a gauntlet since 2002.</p>
      </div>
      <p v-if="shelf.open.length" class="open">Still to earn: <span v-for="x in shelf.open" :key="x.g.id" class="o"><RibbonBadge tier="unclaimed" :size="10" /> {{ x.g.ribbon }}</span></p>
    </section>
    <p v-if="!rows.length" class="empty">{{ team }} didn't play every team in any gauntlet in {{ season }}.</p>
    <article v-for="x in rows" :key="x.g.id" class="g" :class="x.status">
      <div class="top">
        <h3><a :href="`#gauntlet=${x.g.id}`">{{ x.g.name }}</a> <em v-if="x.r?.is_member">member</em></h3>
        <span class="badge">{{ label[x.status] }}</span>
      </div>
      <div class="bar"><i :style="{ width: (100 * x.r.beaten_count) / x.r.required + '%' }"></i></div>
      <p class="n">
        {{ x.r.beaten_count }} of {{ x.r.required }} beaten
        <template v-if="x.status === 'in-progress' && x.next"> · next up: <b>{{ x.next.opp }} ({{ x.next.at }}), {{ x.next.date }}</b></template>
      </p>
      <OpponentRows v-if="games" :team="team" :opps="x.opps" :games="games" :season="season" />
      <p v-else class="n">Loading games…</p>
      <p v-if="x.years.length" class="hist">Completed: {{ x.years.join(', ') }}</p>
    </article>
  </div>
</template>

<style scoped>
.shelf { grid-column:1/-1 } .earned { display:grid; grid-template-columns:repeat(auto-fill,minmax(min(250px,100%),1fr)); gap:8px }
.rib { display:flex; gap:10px; align-items:center; background:#fff; border:1px solid var(--line); padding:8px 10px } .rib small { display:block; color:var(--muted); font-size:.74rem }
.x { font-family:var(--font-mono); font-size:.8rem; background:var(--fg); color:#fff; padding:0 5px }
.open { font-size:.78rem; margin:10px 0 0; color:#3d3d3d } .o { display:inline-block; margin:2px 10px 2px 0; white-space:nowrap }

.pick { display:flex; gap:16px; margin-bottom:12px; flex-wrap:wrap } select { font:inherit; margin-left:6px }
.tv { display:grid; grid-template-columns:repeat(auto-fill,minmax(min(380px,100%),1fr)); gap:14px }
.pick { grid-column:1/-1 }
.g { background:var(--card); border:1px solid var(--line); border-radius:0; padding:12px 14px; border-left:4px solid var(--line) }
.g.complete { border-left-color:var(--ok) } .g.in-progress { border-left-color:var(--warn) } .g.failed { border-left-color:var(--bad) }
.empty { grid-column:1/-1; color:var(--muted) }
.top { display:flex; justify-content:space-between; align-items:center } h3 { margin:0; font-size:1.05rem } h3 a { text-decoration:none }
h3 em { font-style:normal; color:var(--muted); font-size:.75rem; margin-left:4px }
.badge { font-family:var(--font-mono); font-size:.72rem; border:1px solid var(--line); border-radius:0; padding:1px 8px }
.complete .badge { background:var(--ok); color:#fff; border-color:var(--ok) }
.in-progress .badge { background:var(--warn) } .failed .badge { background:var(--bad); color:#fff; border-color:var(--bad) }
.bar { height:6px; background:var(--soft); margin:8px 0 4px; overflow:hidden } .bar i { display:block; height:100%; background:var(--ok) }
.in-progress .bar i { background:var(--warn) } .failed .bar i { background:var(--bad) }
p { margin:3px 0; font-size:.85rem } .n { color:var(--muted) } .n b { color:var(--fg) } .hist { color:var(--muted); font-size:.8rem; margin-top:8px }
</style>
