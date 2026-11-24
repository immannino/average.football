<script setup>
import { ref, computed } from 'vue'
import TeamChip from './TeamChip.vue'
const props = defineProps({ rows: Array, current: Boolean }) // rows: flattened result rows with name, rank, ts
const filter = ref('all')
const sortKey = ref('rank')
const dir = ref(1)

const label = { complete: 'Complete', 'in-progress': props.current ? 'On watch' : 'Alive', failed: 'Failed' }
const order = { complete: 0, 'in-progress': 1, failed: 2 }
const counts = computed(() => ({
  all: props.rows.length,
  complete: props.rows.filter((r) => r.status === 'complete').length,
  'in-progress': props.rows.filter((r) => r.status === 'in-progress').length,
  failed: props.rows.filter((r) => r.status === 'failed').length,
}))
const keyFn = {
  rank: (r) => r.rank,
  team: (r) => r.team,
  status: (r) => order[r.status],
  progress: (r) => r.beaten_count / r.required,
  record: (r) => (r.ts ? r.ts.wins - r.ts.losses : 0),
}
const sorted = computed(() => {
  const f = keyFn[sortKey.value]
  return props.rows
    .filter((r) => filter.value === 'all' || r.status === filter.value)
    .slice()
    .sort((a, b) => {
      const x = f(a), y = f(b)
      const c = x < y ? -1 : x > y ? 1 : 0
      return (c || a.rank - b.rank || order[a.status] - order[b.status] || a.team.localeCompare(b.team)) * (c ? dir.value : 1)
    })
})
const sort = (k) => {
  if (sortKey.value === k) dir.value *= -1
  else { sortKey.value = k; dir.value = k === 'progress' || k === 'record' ? -1 : 1 }
}
const arrow = (k) => (sortKey.value === k ? (dir.value > 0 ? ' ▲' : ' ▼') : '')
const rec = (t) => (t ? `${t.wins}-${t.losses}${t.ties ? '-' + t.ties : ''}` : '')
const split = (s) => (s ? s.split(',') : [])
const filters = computed(() => [
  ['all', 'All'], ['complete', 'Complete'], ['in-progress', props.current ? 'On watch' : 'Alive'], ['failed', 'Failed'],
])
</script>

<template>
  <section class="gt window full" data-title="EVERY TEAM, EVERY GAUNTLET IT QUALIFIES FOR">
    <div class="filters">
      <button v-for="[k, l] in filters" :key="k" :class="{ on: filter === k }" @click="filter = k">{{ l }} <span>{{ counts[k] }}</span></button>
    </div>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th><button @click="sort('rank')">Gauntlet (rarest first){{ arrow('rank') }}</button></th>
            <th><button @click="sort('team')">Team{{ arrow('team') }}</button></th>
            <th><button @click="sort('status')">Status{{ arrow('status') }}</button></th>
            <th><button @click="sort('progress')">Progress{{ arrow('progress') }}</button></th>
            <th>Beaten</th>
            <th>Still needs / missed</th>
            <th><button @click="sort('record')">Record{{ arrow('record') }}</button></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in sorted" :key="r.gauntlet + r.team" :class="r.status">
            <td><a :href="`#gauntlet=${r.gauntlet}`">{{ r.name }}</a> <em>#{{ r.rank }}</em></td>
            <td><TeamChip :team="r.team" bold /><em v-if="r.is_member"> member</em></td>
            <td><span class="st" :class="r.status">{{ label[r.status] }}</span></td>
            <td class="prog"><span class="bar"><i :style="{ width: (100 * r.beaten_count) / r.required + '%' }"></i></span> {{ r.beaten_count }}/{{ r.required }}</td>
            <td><TeamChip v-for="t in split(r.beaten)" :key="t" :team="t" class="ok" /><span v-if="!r.beaten" class="none">none</span></td>
            <td>
              <TeamChip v-for="t in split(r.status === 'failed' ? r.lost_to : r.missing)" :key="t" :team="t" :class="r.status === 'failed' ? 'bad' : ''" />
              <span v-if="r.status === 'complete'" class="none">done</span>
            </td>
            <td>{{ rec(r.ts) }}<span v-if="r.ts?.champion"> 🏆</span></td>
          </tr>
          <tr v-if="!sorted.length"><td colspan="7" class="none">Nothing here.</td></tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.filters { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px }
.filters button { font:inherit; font-family:var(--font-mono); font-size:.8rem; background:#fff; border:1px solid var(--line); border-radius:0; padding:2px 8px; cursor:pointer; color:var(--fg) }
.filters button.on, .filters button:hover { background:var(--fg); color:#fff } .filters span { opacity:.7 }
.scroll { overflow-x:auto }
table { width:100%; border-collapse:collapse; font-size:.85rem; background:#fff; border:1px solid var(--line) }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--soft); vertical-align:top; white-space:nowrap }
td:nth-child(5), td:nth-child(6) { white-space:normal; min-width:130px }
th { background:var(--fg); color:#fff; font-family:var(--font-mono); font-weight:500; font-size:.75rem }
th button { all:unset; cursor:pointer } th button:hover { text-decoration:underline }
em { font-style:normal; color:var(--muted); font-size:.72rem }
.st { font-family:var(--font-mono); font-size:.72rem; padding:1px 6px; border:1px solid var(--line); color:#fff }
.st.complete { background:var(--ok) } .st.in-progress { background:var(--warn); color:var(--fg) } .st.failed { background:var(--bad) }
tr.failed td { color:var(--muted) } tr.failed .chip, tr.failed a { color:var(--muted) }
.chip.ok { border-color:var(--ok) } .chip.bad { border-color:var(--bad) }
.bar { display:inline-block; vertical-align:middle; width:56px; height:6px; background:#fff; border:1px solid var(--line) } .bar i { display:block; height:100%; background:var(--warn) }
tr.complete .bar i { background:var(--ok) } tr.failed .bar i { background:var(--bad) }
.none { color:var(--muted) }
</style>
