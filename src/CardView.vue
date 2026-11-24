<script setup>
// 1080x1350 share cards, screenshotted by scripts/cards.mjs. Routes: #card=watch, #card=e0, #card=e1, ...
import { ref, computed, onMounted, inject } from 'vue'
import RibbonBadge from './RibbonBadge.vue'
import TeamChip from './TeamChip.vue'
import { tierOf, TIERS } from './stats.js'
const props = defineProps({ id: String, gauntlets: Array, results: Array, seasons: Array })
const rarity = inject('rarity', ref({}))
const digest = ref(null)
onMounted(async () => {
  try { digest.value = await fetch(`${import.meta.env.BASE_URL}data/digest.json`).then((r) => r.json()) } catch { digest.value = { events: [] } }
})
const season = computed(() => props.seasons[0])
const g = (id) => props.gauntlets.find((x) => x.id === id)

const event = computed(() => (props.id?.startsWith('e') && digest.value ? digest.value.events[Number(props.id.slice(1))] : null))
const eg = computed(() => (event.value ? g(event.value.gauntlet) : null))
const er = computed(() => (event.value ? rarity.value[event.value.gauntlet] : null))
const dt = (iso) => new Date(iso + 'T12:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
const headline = computed(() => ({ complete: 'Gauntlet complete.', one_away: 'One win away.', failed: 'Not this year.' }[event.value?.kind] || ''))

const watch = computed(() => {
  const rows = props.results.filter((r) => r.season === season.value)
  const list = props.gauntlets
    .map((gx) => ({ g: gx, h: rarity.value[gx.id], alive: rows.filter((r) => r.gauntlet === gx.id && r.status === 'in-progress').sort((a, b) => b.beaten_count / b.required - a.beaten_count / a.required) }))
    .filter((x) => x.alive.length)
    .sort((a, b) => a.h.rank - b.h.rank)
  return { list, teams: new Set(list.flatMap((x) => x.alive.map((r) => r.team))).size }
})
</script>

<template>
  <div class="stage">
    <div class="top">
      <span class="brand"><img src="/favicon.svg" alt="" width="40" />average<span>.football</span></span>
      <span class="when" v-if="digest">{{ season }} season · as of {{ dt(digest.as_of) }}</span>
    </div>

    <template v-if="id === 'watch'">
      <h1>Gauntlet Watch</h1>
      <p class="sub">{{ watch.teams }} teams still chasing {{ watch.list.length }} gauntlets. Rarest first.</p>
      <div class="win" v-for="x in watch.list.slice(0, 3)" :key="x.g.id" :data-title="`${x.g.name.toUpperCase()} GAUNTLET · #${x.h.rank} OF ${gauntlets.length} RAREST`">
        <div class="wh"><RibbonBadge :tier="tierOf(x.h)" :size="44" /><div><b>{{ x.g.ribbon }}</b><small>Beat all {{ x.g.teams.length }}: {{ x.g.teams.join(' · ') }}</small></div></div>
        <div class="alive" v-for="r in x.alive.slice(0, 3)" :key="r.team">
          <TeamChip :team="r.team" bold /> <span class="n">{{ r.beaten_count }}/{{ r.required }}</span>
          <span class="need">needs {{ r.missing.split(',').join(', ') }}</span>
        </div>
        <p v-if="x.alive.length > 3" class="more">+{{ x.alive.length - 3 }} more</p>
      </div>
      <p v-if="watch.list.length > 3" class="more">+{{ watch.list.length - 3 }} more gauntlets on the site</p>
    </template>

    <template v-else-if="event && eg">
      <h1>{{ headline }}</h1>
      <p class="sub"><b>{{ event.team_name }}</b>
        <template v-if="event.kind === 'complete'"> beat every team in the {{ eg.name }} gauntlet ({{ event.record }}).</template>
        <template v-else-if="event.kind === 'one_away'"> has beaten {{ event.beaten }} of {{ event.required }} in the {{ eg.name }} gauntlet.</template>
        <template v-else> missed {{ event.lost_to.join(', ') }} in the {{ eg.name }} gauntlet.</template></p>
      <div class="win big" :data-title="`${eg.name.toUpperCase()} GAUNTLET · #${er.rank} OF ${gauntlets.length} RAREST`">
        <div class="hero">
          <RibbonBadge :tier="tierOf(er)" :size="150" :style="{ opacity: event.kind === 'complete' ? 1 : 0.45 }" />
          <div><b>{{ eg.ribbon }}</b><small>{{ event.kind === 'complete' ? TIERS[tierOf(er)].label + ' ribbon earned' : 'Ribbon on the line' }}</small></div>
        </div>
        <p class="line">Must beat all {{ eg.teams.length }}:</p>
        <div class="chips"><TeamChip v-for="t in eg.teams" :key="t" :team="t" /></div>
        <p v-if="event.kind === 'one_away' && event.next" class="line need2">Needs {{ event.missing.join(', ') }}. Next game: <b>{{ event.next.home ? 'vs' : '@' }} {{ event.next.opp }}, {{ dt(event.next.date) }}</b></p>
        <p v-else-if="event.kind === 'one_away'" class="line need2">Needs {{ event.missing.join(', ') }}.</p>
        <p class="line">Done {{ er.done }} time{{ er.done === 1 ? '' : 's' }} in {{ er.attempts }} attempts since 2002.</p>
      </div>
    </template>
    <p v-else class="sub">Loading card…</p>

    <div class="foot">www.average.football</div>
  </div>
</template>

<style scoped>
.stage { width:1080px; height:1350px; overflow:hidden; position:relative; padding:48px 56px; box-sizing:border-box;
  background:#fff url('/textures/pixel-sky.png') top left / 100% 700px no-repeat; image-rendering:pixelated }
.top { display:flex; justify-content:space-between; align-items:center }
.brand, .when { background:#fff; padding:6px 14px; font-size:30px; font-weight:500; letter-spacing:-.03em } .brand span { color:var(--accent) } .brand img { image-rendering:pixelated; vertical-align:-6px; margin-right:10px }
.when { font-family:var(--font-mono); font-size:22px; letter-spacing:0 }
h1 { margin:90px 0 10px; font-size:120px; line-height:.92; letter-spacing:-.05em; font-weight:500; background:none }
.sub { font-family:var(--font-sans); text-transform:none; letter-spacing:0; font-weight:500; color:var(--fg); margin-top:0; display:inline-block; background:#fff; margin:0 0 28px; padding:6px 14px; font-size:34px; line-height:1.3 }
.win { position:relative; background:#dcdcdc; border:2px solid var(--line); outline:2px solid var(--line); outline-offset:4px; padding:0 24px 20px; margin:0 6px 28px }
.win::before { content:attr(data-title); display:block; margin:0 -24px 16px; padding:4px 14px; background:var(--fg); color:#fff; font-family:var(--font-mono); font-size:22px }
.wh, .hero { display:flex; gap:18px; align-items:center } .wh b { font-size:38px; letter-spacing:-.02em } .wh small, .hero small { display:block; font-size:22px; color:#3d3d3d }
.alive { display:flex; gap:16px; align-items:center; background:#fff; border:2px solid var(--line); padding:6px 14px; margin-top:10px; font-size:28px }
.alive .n { font-family:var(--font-mono) } .need { color:#3d3d3d; font-size:24px }
.more { margin:8px 0 0; font-size:24px; background:#fff; display:inline-block; padding:2px 10px }
.win.big { margin-top:10px } .hero b { font-size:64px; letter-spacing:-.04em; line-height:1 } .hero small { font-size:28px; margin-top:6px }
.line { font-size:30px; margin:18px 0 8px } .need2 { background:#f2c200; display:inline-block; padding:4px 12px }
.chips { font-size:30px }
.foot { position:absolute; bottom:40px; left:56px; right:56px; text-align:center; font-family:var(--font-mono); font-size:30px }
.stage :deep(.chip) { font-size:26px; padding:2px 10px; margin-right:6px } .stage :deep(.chip img) { width:30px; height:30px; vertical-align:-7px }
</style>
