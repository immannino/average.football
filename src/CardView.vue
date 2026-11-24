<script setup>
// Share cards, screenshotted by scripts/cards.mjs.
//   #card=watch | e0, e1, ... (digest events) | c0, c1, ... (carousel slides: cover, one per live gauntlet, closer)
//   optional size suffix: @post (1080x1350, default) | @story (1080x1920) | @square (1080x1080)
import { ref, computed, onMounted, inject } from 'vue'
import RibbonBadge from './RibbonBadge.vue'
import TeamChip from './TeamChip.vue'
import { tierOf, TIERS } from './stats.js'
import { loadGames, teamGames, opponentRows } from './games.js'

const props = defineProps({ id: String, gauntlets: Array, results: Array, seasons: Array })
const rarity = inject('rarity', ref({}))
const digest = ref(null), games = ref(null)
onMounted(async () => {
  try { digest.value = await fetch(`${import.meta.env.BASE_URL}data/digest.json`).then((r) => r.json()) } catch { digest.value = { events: [] } }
  games.value = await loadGames()
})

const parts = computed(() => {
  const [base, size = 'post'] = (props.id || '').split('@')
  return { base, size: ['post', 'story', 'square'].includes(size) ? size : 'post' }
})
const size = computed(() => parts.value.size)
const SHOW = { post: { windows: 3, teams: 3, slideTeams: 6 }, story: { windows: 4, teams: 3, slideTeams: 8 }, square: { windows: 2, teams: 2, slideTeams: 4 } }
const show = computed(() => SHOW[size.value])

const season = computed(() => props.seasons[0])
const g = (id) => props.gauntlets.find((x) => x.id === id)
const dt = (iso) => new Date(iso + 'T12:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

// ---- single event cards
const event = computed(() => (/^e\d+$/.test(parts.value.base) && digest.value ? digest.value.events[Number(parts.value.base.slice(1))] : null))
const eg = computed(() => (event.value ? g(event.value.gauntlet) : null))
const er = computed(() => (event.value ? rarity.value[event.value.gauntlet] : null))
const headline = computed(() => ({ complete: 'Gauntlet complete.', one_away: 'One win away.', failed: 'Not this year.' }[event.value?.kind] || ''))

// ---- live gauntlets (shared by the watch card and the carousel)
const watch = computed(() => {
  const rows = props.results.filter((r) => r.season === season.value)
  const list = props.gauntlets
    .map((gx) => ({ g: gx, h: rarity.value[gx.id], alive: rows.filter((r) => r.gauntlet === gx.id && r.status === 'in-progress').sort((a, b) => b.beaten_count / b.required - a.beaten_count / a.required) }))
    .filter((x) => x.alive.length)
    .sort((a, b) => a.h.rank - b.h.rank)
  return { list, teams: new Set(list.flatMap((x) => x.alive.map((r) => r.team))).size }
})
// where a chasing team plays its missing opponents next
const nexts = (r, gx) => {
  if (!games.value) return r.missing.split(',').join(', ')
  const rows = opponentRows(teamGames(games.value, r.team, season.value), gx.teams.filter((t) => t !== r.team)).filter((o) => o.state === 'next')
  return rows.map((o) => `${o.o} ${o.next.date} ${o.next.at === 'home' ? 'home' : 'away'}`).join(' · ')
}

// ---- carousel
const N = computed(() => Math.min(8, watch.value.list.length))
const slide = computed(() => {
  const m = parts.value.base.match(/^c(\d+)$/)
  if (!m) return null
  const i = Number(m[1])
  return i === 0 ? { kind: 'cover' } : i <= N.value ? { kind: 'gauntlet', i, x: watch.value.list[i - 1] } : { kind: 'outro' }
})
const pager = computed(() => (slide.value ? `${Number(parts.value.base.slice(1)) + 1}/${N.value + 2}` : ''))
</script>

<template>
  <div class="stage" :class="size">
    <div class="top">
      <span class="brand"><img src="/favicon.svg" alt="" width="40" />average<span>.football</span></span>
      <span class="when" v-if="pager">{{ pager }}</span>
      <span class="when" v-else-if="digest">{{ season }} season · as of {{ dt(digest.as_of) }}</span>
    </div>

    <!-- watch summary -->
    <template v-if="parts.base === 'watch'">
      <h1>Gauntlet Watch</h1>
      <p class="sub">{{ watch.teams }} teams still chasing {{ watch.list.length }} gauntlets. Rarest first.</p>
      <div class="win" v-for="x in watch.list.slice(0, show.windows)" :key="x.g.id" :data-title="`${x.g.name.toUpperCase()} GAUNTLET · #${x.h.rank} OF ${gauntlets.length} RAREST`">
        <div class="wh"><RibbonBadge :tier="tierOf(x.h)" :size="size === 'square' ? 36 : 44" /><div><b>{{ x.g.ribbon }}</b><small>Beat all {{ x.g.teams.length }}: {{ x.g.teams.join(' · ') }}</small></div></div>
        <div class="alive" v-for="r in x.alive.slice(0, show.teams)" :key="r.team">
          <TeamChip :team="r.team" bold /> <span class="n">{{ r.beaten_count }}/{{ r.required }}</span>
          <span class="need">needs {{ r.missing.split(',').join(', ') }}</span>
        </div>
        <p v-if="x.alive.length > show.teams" class="more">+{{ x.alive.length - show.teams }} more</p>
      </div>
      <p v-if="watch.list.length > show.windows" class="more">+{{ watch.list.length - show.windows }} more gauntlets on the site</p>
    </template>

    <!-- carousel: cover -->
    <template v-else-if="slide?.kind === 'cover'">
      <h1>Gauntlet Watch</h1>
      <p class="sub">{{ watch.teams }} teams are still chasing {{ watch.list.length }} gauntlets. Swipe for who needs what.</p>
      <div class="ribbons">
        <div class="ribitem" v-for="x in watch.list.slice(0, 8)" :key="x.g.id"><RibbonBadge :tier="tierOf(x.h)" :size="52" /><span><b>{{ x.g.ribbon }}</b><small>{{ x.alive.length }} chasing</small></span></div>
      </div>
      <p class="swipe">swipe →</p>
    </template>

    <!-- carousel: one gauntlet -->
    <template v-else-if="slide?.kind === 'gauntlet'">
      <p class="kicker">GAUNTLET #{{ slide.x.h.rank }} OF {{ gauntlets.length }} RAREST</p>
      <h1 class="mid">{{ slide.x.g.ribbon }}</h1>
      <p class="sub">{{ slide.x.g.name }} gauntlet · done {{ slide.x.h.done }} time{{ slide.x.h.done === 1 ? '' : 's' }} in {{ slide.x.h.attempts }} attempts since 2002</p>
      <div class="win" :data-title="`BEAT ALL ${slide.x.g.teams.length}`">
        <div class="chips"><TeamChip v-for="t in slide.x.g.teams" :key="t" :team="t" /></div>
        <p class="line">Still chasing it ({{ slide.x.alive.length }}):</p>
        <div class="alive" v-for="r in slide.x.alive.slice(0, show.slideTeams)" :key="r.team">
          <TeamChip :team="r.team" bold /> <span class="n">{{ r.beaten_count }}/{{ r.required }}</span>
          <span class="need">{{ nexts(r, slide.x.g) }}</span>
        </div>
        <p v-if="slide.x.alive.length > show.slideTeams" class="more">+{{ slide.x.alive.length - show.slideTeams }} more on the site</p>
      </div>
    </template>

    <!-- carousel: closer -->
    <template v-else-if="slide?.kind === 'outro'">
      <h1>What's a gauntlet?</h1>
      <div class="win" data-title="THE RULES">
        <p class="line">A group of teams with something in common: birds, cats, mythical creatures, and guys.</p>
        <p class="line">Beat <b>every team in the group</b> in one season (regular season or playoffs) and you earn the ribbon.</p>
        <p class="line">It almost never happens. Rarer gauntlets earn shinier ribbons.</p>
        <div class="tiers"><span v-for="t in ['bronze', 'silver', 'gold', 'legendary']" :key="t"><RibbonBadge :tier="t" :size="40" /> {{ TIERS[t].label }}</span></div>
      </div>
    </template>

    <!-- one digest event -->
    <template v-else-if="event && eg">
      <h1>{{ headline }}</h1>
      <p class="sub"><b>{{ event.team_name }}</b>
        <template v-if="event.kind === 'complete'"> beat every team in the {{ eg.name }} gauntlet ({{ event.record }}).</template>
        <template v-else-if="event.kind === 'one_away'"> has beaten {{ event.beaten }} of {{ event.required }} in the {{ eg.name }} gauntlet.</template>
        <template v-else> missed {{ event.lost_to.join(', ') }} in the {{ eg.name }} gauntlet.</template></p>
      <div class="win big" :data-title="`${eg.name.toUpperCase()} GAUNTLET · #${er.rank} OF ${gauntlets.length} RAREST`">
        <div class="hero">
          <RibbonBadge :tier="tierOf(er)" :size="size === 'square' ? 100 : 150" :style="{ opacity: event.kind === 'complete' ? 1 : 0.45 }" />
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
.stage.story { height:1920px; padding:200px 56px 48px; background-size:100% 1000px }
.stage.square { height:1080px; padding:36px 56px; background-size:100% 520px }
.top { display:flex; justify-content:space-between; align-items:center }
.story .top { position:absolute; top:200px; left:56px; right:56px }
.story h1 { margin-top:150px }
.brand, .when { background:#fff; padding:6px 14px; font-size:30px; font-weight:500; letter-spacing:-.03em } .brand span { color:var(--accent) } .brand img { image-rendering:pixelated; vertical-align:-6px; margin-right:10px }
.when { font-family:var(--font-mono); font-size:22px; letter-spacing:0 }
h1 { margin:90px 0 10px; font-size:120px; line-height:.92; letter-spacing:-.05em; font-weight:500; background:none }
h1.mid { font-size:100px; margin-top:40px }
.square h1 { margin-top:46px; font-size:92px } .square h1.mid { font-size:80px; margin-top:30px }
.sub { font-family:var(--font-sans); text-transform:none; letter-spacing:0; font-weight:500; color:var(--fg); margin-top:0; display:inline-block; background:#fff; margin-bottom:28px; padding:6px 14px; font-size:34px; line-height:1.3 }
.square .sub { font-size:28px; margin-bottom:20px }
.kicker { display:inline-block; margin:70px 0 0; background:var(--fg); color:#fff; padding:4px 14px; font-family:var(--font-mono); font-size:24px } .square .kicker { margin-top:30px }
h1 + .win { margin-top:36px }
.win { position:relative; background:#dcdcdc; border:2px solid var(--line); outline:2px solid var(--line); outline-offset:4px; padding:0 24px 20px; margin:0 6px 28px }
.square .win { margin-bottom:20px; padding-bottom:12px }
.win::before { content:attr(data-title); display:block; margin:0 -24px 16px; padding:4px 14px; background:var(--fg); color:#fff; font-family:var(--font-mono); font-size:22px }
.wh, .hero { display:flex; gap:18px; align-items:center } .wh b { font-size:38px; letter-spacing:-.02em } .wh small, .hero small { display:block; font-size:22px; color:#3d3d3d }
.alive { display:flex; gap:16px; align-items:center; flex-wrap:wrap; background:#fff; border:2px solid var(--line); padding:6px 14px; margin-top:10px; font-size:28px }
.alive .n { font-family:var(--font-mono) } .need { color:#3d3d3d; font-size:24px }
.more { margin:8px 0 0; font-size:24px; background:#fff; display:inline-block; padding:2px 10px }
.win.big { margin-top:10px } .hero b { font-size:64px; letter-spacing:-.04em; line-height:1 } .square .hero b { font-size:48px } .hero small { font-size:28px; margin-top:6px }
.line { font-size:30px; margin:18px 0 8px } .square .line { font-size:26px; margin:10px 0 6px } .need2 { background:#f2c200; display:inline-block; padding:4px 12px }
.chips { font-size:30px }
.ribbons { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:10px 6px 0 }
.ribitem { display:flex; gap:14px; align-items:center; background:#fff; border:2px solid var(--line); padding:10px 14px } .ribitem b { display:block; font-size:30px; letter-spacing:-.02em; line-height:1.1 } .ribitem small { color:#3d3d3d; font-size:22px }
.swipe { position:absolute; right:56px; bottom:110px; margin:0; background:var(--fg); color:#fff; padding:6px 18px; font-family:var(--font-mono); font-size:30px }
.tiers { display:flex; gap:26px; flex-wrap:wrap; margin-top:20px; font-family:var(--font-mono); font-size:26px } .tiers span { display:flex; align-items:center; gap:8px; background:#fff; padding:6px 12px; border:2px solid var(--line) }
.foot { position:absolute; bottom:40px; left:56px; right:56px; text-align:center; font-family:var(--font-mono); font-size:30px }
.story .foot { bottom:200px } .square .foot { bottom:24px; font-size:24px }
.stage :deep(.chip) { font-size:26px; padding:2px 10px; margin-right:6px } .stage :deep(.chip img) { width:30px; height:30px; vertical-align:-7px }
</style>
