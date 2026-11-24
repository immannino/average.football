<script setup>
import { computed } from 'vue'
import TeamChip from './TeamChip.vue'
const props = defineProps({ gauntlets: Array, results: Array, seasons: Array, rarity: Object })
const live = computed(() => props.seasons[0])
const rows = computed(() =>
  props.gauntlets.map((g) => {
    const rs = props.results.filter((r) => r.gauntlet === g.id)
    const done = rs.filter((r) => r.complete)
    const now = rs.filter((r) => r.season === live.value)
    const last = done.map((r) => r.season).sort((a, b) => b - a)[0]
    const state = now.some((r) => r.status === 'complete') ? 'complete' : now.some((r) => r.status === 'in-progress') ? 'watch' : 'out'
    return { g, r: props.rarity[g.id], done: done.length, last, state, alive: now.filter((r) => r.status === 'in-progress').length }
  }).sort((a, b) => a.r.rank - b.r.rank),
)
const label = { complete: 'Complete', watch: 'On watch', out: 'Out of reach' }
</script>

<template>
  <section class="window" data-title="ALL GAUNTLETS · RAREST FIRST">
    <div class="scroll">
      <table>
        <thead><tr><th>#</th><th>Gauntlet</th><th>Teams you must beat</th><th>Completed</th><th>Last</th><th>{{ live }}</th></tr></thead>
        <tbody>
          <tr v-for="x in rows" :key="x.g.id">
            <td>{{ x.r.rank }}</td>
            <td><a :href="`#gauntlet=${x.g.id}`" class="name">{{ x.g.name }}</a><em class="sz">{{ x.g.teams.length }} teams</em></td>
            <td class="tm"><TeamChip v-for="t in x.g.teams" :key="t" :team="t" /></td>
            <td v-if="x.r.attempts">{{ x.done }}<em> of {{ x.r.attempts }} attempts</em></td>
            <td v-else><em>no team ever played all {{ x.g.teams.length }}</em></td>
            <td>{{ x.last ?? '—' }}</td>
            <td><span class="st" :class="x.state">{{ label[x.state] }}</span><em v-if="x.alive" class="sz">{{ x.alive }} alive</em></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.scroll { overflow-x:auto }
table { width:100%; border-collapse:collapse; font-size:.85rem; background:#fff; border:1px solid var(--line) }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--soft); vertical-align:top }
.tm { min-width:180px } th { background:var(--fg); color:#fff; font-family:var(--font-mono); font-weight:500; font-size:.75rem; white-space:nowrap }
.name { font-weight:700 } em.sz { display:block } em { font-style:normal; color:var(--muted); font-size:.72rem }
.st { font-family:var(--font-mono); font-size:.72rem; padding:1px 6px; border:1px solid var(--line); color:#fff; white-space:nowrap }
.st.complete { background:var(--ok) } .st.watch { background:var(--warn); color:var(--fg) } .st.out { background:#fff; color:var(--muted) }
</style>
