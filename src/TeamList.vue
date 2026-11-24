<script setup>
import { ref, computed } from 'vue'
import { teamName } from './teamNames.js'
import TeamChip from './TeamChip.vue'
const props = defineProps({ teams: Array, results: Array, seasons: Array, teamSeasons: Array })
const live = computed(() => props.seasons[0])
const sortKey = ref('team'), dir = ref(1)
const rows = computed(() => {
  const ts = new Map(props.teamSeasons.filter((x) => x.season === live.value).map((x) => [x.team, x]))
  return props.teams.map((t) => {
    const mine = props.results.filter((r) => r.team === t)
    const now = mine.filter((r) => r.season === live.value)
    const done = mine.filter((r) => r.complete)
    const last = done.slice().sort((a, b) => b.season - a.season)[0]
    return { t, rec: ts.get(t), done: done.length, last, c: now.filter((r) => r.status === 'complete').length,
      w: now.filter((r) => r.status === 'in-progress').length, f: now.filter((r) => r.status === 'failed').length }
  })
})
const val = { team: (r) => r.t, done: (r) => r.done, c: (r) => r.c, w: (r) => r.w, f: (r) => r.f }
const sorted = computed(() => rows.value.slice().sort((a, b) => {
  const x = val[sortKey.value](a), y = val[sortKey.value](b)
  return ((x < y ? -1 : x > y ? 1 : 0) || a.t.localeCompare(b.t)) * dir.value
}))
const sort = (k) => { if (sortKey.value === k) dir.value *= -1; else { sortKey.value = k; dir.value = k === 'team' ? 1 : -1 } }
const arrow = (k) => (sortKey.value === k ? (dir.value > 0 ? ' ▲' : ' ▼') : '')
const rec = (t) => (t ? `${t.wins}-${t.losses}${t.ties ? '-' + t.ties : ''}` : '—')
</script>

<template>
  <section class="window" data-title="ALL 32 TEAMS">
    <div class="scroll">
      <table>
        <thead><tr>
          <th><button @click="sort('team')">Team{{ arrow('team') }}</button></th>
          <th>{{ live }}</th>
          <th><button @click="sort('done')">Completed since 2002{{ arrow('done') }}</button></th>
          <th>Most recent</th>
          <th><button @click="sort('c')">Complete{{ arrow('c') }}</button></th>
          <th><button @click="sort('w')">On watch{{ arrow('w') }}</button></th>
          <th><button @click="sort('f')">Failed{{ arrow('f') }}</button></th>
        </tr></thead>
        <tbody>
          <tr v-for="x in sorted" :key="x.t">
            <td><TeamChip :team="x.t" bold /> <span class="nm">{{ teamName(x.t) }}</span></td>
            <td>{{ rec(x.rec) }}</td>
            <td>{{ x.done }}</td>
            <td>{{ x.last ? `${x.last.season}` : '—' }}</td>
            <td><span v-if="x.c" class="n ok">{{ x.c }}</span><span v-else class="z">0</span></td>
            <td><span v-if="x.w" class="n warn">{{ x.w }}</span><span v-else class="z">0</span></td>
            <td><span v-if="x.f" class="n bad">{{ x.f }}</span><span v-else class="z">0</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.scroll { overflow-x:auto }
table { width:100%; border-collapse:collapse; font-size:.85rem; background:#fff; border:1px solid var(--line) }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--soft); white-space:nowrap }
th { background:var(--fg); color:#fff; font-family:var(--font-mono); font-weight:500; font-size:.75rem }
th button { all:unset; cursor:pointer } th button:hover { text-decoration:underline }
.nm { color:var(--muted); font-size:.8rem } .z { color:var(--muted) }
.n { font-family:var(--font-mono); font-size:.75rem; padding:1px 8px; border:1px solid var(--line); color:#fff }
.n.ok { background:var(--ok) } .n.warn { background:var(--warn); color:var(--fg) } .n.bad { background:var(--bad) }
</style>
