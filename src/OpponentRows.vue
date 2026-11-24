<script setup>
import { computed } from 'vue'
import TeamChip from './TeamChip.vue'
import { teamGames, opponentRows } from './games.js'
const props = defineProps({ team: String, opps: Array, games: Array, season: Number, compact: Boolean })
const rows = computed(() => opponentRows(teamGames(props.games, props.team, props.season), props.opps.filter((o) => o !== props.team)))
const stateLabel = { beaten: 'Beaten', next: 'Next up', lost: 'Lost, no rematch', none: '—' }
const mark = { beaten: '✓', next: '→', lost: '✗', none: '' }
</script>

<template>
  <table class="opp" :class="{ compact }">
    <tbody>
      <tr v-for="o in rows" :key="o.o" :class="o.state">
        <td class="o"><span v-if="compact" class="mk">{{ mark[o.state] }}</span><TeamChip :team="o.o" /></td>
        <td class="gm">
          <span v-for="(g, i) in o.gs" :key="i" class="game" :class="g.res">
            <b>{{ g.res === 'next' ? '' : g.res }}</b>
            {{ g.res === 'next' ? `${g.date} · ${g.at}` : `${g.score} · ${g.date} · ${g.at}` }}<em v-if="g.post"> playoffs</em>
          </span>
        </td>
        <td v-if="!compact" class="s"><span class="st" :class="o.state">{{ stateLabel[o.state] }}</span></td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
table { width:100%; border-collapse:collapse; margin-top:6px; font-size:.82rem }
td { padding:4px 4px; border-top:1px solid var(--soft); vertical-align:top }
.compact td { border-top-color:#bdbdbd; padding:3px 4px; font-size:.78rem }
td.o { width:78px; white-space:nowrap } .compact td.o { width:92px } td.s { text-align:right; white-space:nowrap }
.mk { display:inline-block; width:1.1em; font-family:var(--font-mono) }
.game { display:block } .game b { display:inline-block; width:1.1em; font-family:var(--font-mono) }
.game.W b { color:var(--ok) } .game.L b { color:var(--bad) } .game em { font-style:normal; color:var(--muted); font-size:.72rem }
.st { font-family:var(--font-mono); font-size:.7rem; padding:1px 6px; border:1px solid var(--line); background:#fff }
.st.beaten { background:var(--ok); color:#fff; border-color:var(--ok) } .st.next { background:var(--warn) } .st.lost { background:var(--bad); color:#fff; border-color:var(--bad) }
tr.beaten td.o :deep(.chip) { border-color:var(--ok) } tr.lost { color:var(--muted) } tr.lost .mk { color:var(--bad) } tr.beaten .mk { color:var(--ok) }
tr.next { background:color-mix(in srgb, var(--warn) 18%, transparent) }
</style>
