<script setup>
import { ref, computed, watch, inject } from 'vue'
import RibbonBadge from './RibbonBadge.vue'
import { tierOf, TIERS, tierNote } from './stats.js'
import TeamChip from './TeamChip.vue'
const props = defineProps({ gauntlets: Array, results: Array, seasons: Array, initial: String })
const id = ref(props.gauntlets.some((g) => g.id === props.initial) ? props.initial : props.gauntlets[0].id)
watch(() => props.initial, (v) => v && props.gauntlets.some((g) => g.id === v) && (id.value = v))
watch(id, (v) => (location.hash = `#gauntlet=${v}`))

const rarity = inject('rarity', ref({}))
const tier = computed(() => tierOf(rarity.value[id.value]))
const g = computed(() => props.gauntlets.find((x) => x.id === id.value))
const latest = computed(() => props.seasons[0])
const rows = computed(() => props.results.filter((r) => r.gauntlet === id.value))
const timeline = computed(() =>
  props.seasons.map((s) => {
    const r = rows.value.filter((x) => x.season === s)
    return {
      season: s,
      done: r.filter((x) => x.status === 'complete'),
      alive: r.filter((x) => x.status === 'in-progress'),
      failed: r.filter((x) => x.status === 'failed'),
      qualified: r.length,
    }
  }),
)
const done = computed(() => rows.value.filter((r) => r.complete))
const stats = computed(() => {
  const by = {}
  done.value.forEach((r) => (by[r.team] = (by[r.team] || 0) + 1))
  const top = Object.entries(by).sort((a, b) => b[1] - a[1])[0]
  return {
    total: done.value.length,
    years: new Set(done.value.map((r) => r.season)).size,
    champs: done.value.filter((r) => r.ts?.champion).length,
    top: top ? `${top[0]} (${top[1]})` : '—',
    drought: timeline.value.filter((t) => !t.done.length && !t.alive.length).length,
  }
})
const rec = (t) => (t ? `${t.wins}-${t.losses}${t.ties ? '-' + t.ties : ''}` : '')
</script>

<template>
  <div class="gv">
    <label class="chip-label inline">Gauntlet
      <select v-model="id"><option v-for="x in gauntlets" :key="x.id" :value="x.id">{{ x.name }}</option></select>
    </label>

    <section class="explain card">
      <div class="ribbon-row" :title="tierNote">
        <RibbonBadge :tier="tier" :size="40" />
        <div><b>{{ g.ribbon }}</b><small>{{ TIERS[tier].label }} ribbon{{ tier === 'unclaimed' ? ': nobody has earned it since 2002' : '' }}</small></div>
      </div>
      
      <p class="teams"><TeamChip v-for="t in g.teams" :key="t" :team="t" /></p>
      <p>A team completes it by <b>beating every one of these {{ g.teams.length }} teams in the same season</b>
        (regular season or playoffs, ties don't count). Teams in the group only need to beat the other {{ g.teams.length - 1 }}.
        A team only <i>qualifies</i> if its schedule includes all of them.</p>
      <p class="legend"><span class="dot complete"></span>complete <span class="dot alive"></span>still alive (live season)
        <span class="dot failed"></span>failed (lost to one with no game left)</p>
    </section>

    <section class="stats">
      <div><b>{{ stats.total }}</b><span>completions</span></div>
      <div><b>{{ stats.years }}</b><span>seasons with one</span></div>
      <div><b>{{ stats.drought }}</b><span>seasons with none</span></div>
      <div><b>{{ stats.champs }}</b><span>won the title</span></div>
      <div><b>{{ stats.top }}</b><span>most often</span></div>
    </section>

    <section class="card">
      <h2>Season by season</h2>
      <table>
        <thead><tr><th>Season</th><th>Qualified</th><th>Completed</th><th>Alive</th><th>Failed</th></tr></thead>
        <tbody>
          <tr v-for="t in timeline" :key="t.season" :class="{ hit: t.done.length, live: t.season === latest }">
            <td>{{ t.season }}<small v-if="t.season === latest"> live</small></td>
            <td>{{ t.qualified || '—' }}</td>
            <td>
              <template v-if="t.done.length">
                <span v-for="r in t.done" :key="r.team" class="chip complete">
                  <a :href="`#team=${r.team}`">{{ r.team }}</a> {{ rec(r.ts) }}<span v-if="r.ts?.champion"> 🏆</span><em v-if="r.is_member"> member</em>
                </span>
              </template>
              <span v-else class="none">{{ t.qualified ? 'none' : 'no team qualified' }}</span>
            </td>
            <td><a v-for="r in t.alive" :key="r.team" :href="`#team=${r.team}`" class="chip alive">{{ r.team }} {{ r.beaten_count }}/{{ r.required }}</a></td>
            <td><a v-for="r in t.failed" :key="r.team" :href="`#team=${r.team}`" class="chip failed">{{ r.team }}</a></td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.ribbon-row { display:flex; gap:12px; align-items:center; margin-bottom:8px } .ribbon-row b { font-size:1.15rem } .ribbon-row small { display:block; color:var(--muted); font-size:.8rem }

.gv { display:grid; gap:16px } select { font:inherit; margin-left:6px }
.card { background:var(--card); border:1px solid var(--line); border-radius:0; padding:16px; overflow-x:auto }
h2 { margin:0 0 6px; font-size:1.2rem } .teams { color:var(--muted) } p { margin:6px 0; font-size:.9rem }
.legend { color:var(--muted); font-size:.8rem } .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin:0 4px 0 10px; vertical-align:middle }
.dot.complete { background:var(--ok) } .dot.alive { background:var(--warn) } .dot.failed { background:var(--bad) }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:10px }
.stats div { background:var(--card); border:1px solid var(--line); border-radius:0; padding:10px; text-align:center }
.stats b { display:block; font-size:1.3rem; color:var(--ok) } .stats span { color:var(--muted); font-size:.75rem }
table { width:100%; border-collapse:collapse; font-size:.85rem } th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--soft); vertical-align:top }
tr.hit td:first-child { font-weight:700 } tr.live { background:color-mix(in srgb, var(--ok) 8%, transparent) }
.none { color:var(--muted) } small { color:var(--ok) }
.chip { display:inline-block; border-radius:0; padding:0 8px; margin:0 4px 2px 0; border:1px solid var(--line); font-size:.8rem; color:var(--fg); text-decoration:none }
.chip.complete { border-color:var(--ok) } .chip.alive { border-color:var(--warn) } .chip.failed { border-color:var(--bad); color:var(--muted) }
em { font-style:normal; color:var(--muted); font-size:.7rem } a { color:inherit }
</style>
