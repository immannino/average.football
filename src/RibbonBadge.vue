<script setup>
import { computed } from 'vue'
import { TIERS } from './stats.js'
const props = defineProps({ tier: { type: String, default: 'bronze' }, size: { type: Number, default: 28 } })
const W = 14, H = 21
// pixel rosette (circle) with two tails; colors come from the tier
const cells = computed(() => {
  const t = TIERS[props.tier] || TIERS.bronze
  const out = []
  const filled = new Set()
  for (let y = 0; y < 14; y++) for (let x = 0; x < W; x++) if (Math.hypot(x - 6.5, y - 6.5) <= 6.6) filled.add(`${x},${y}`)
  for (let y = 12; y < H; y++) {
    const notch = y >= 18 ? y - 17 : 0
    for (let x = 2; x < 12; x++) {
      const inLeft = x >= 2 && x <= 6 && !(x > 6 - notch), inRight = x >= 7 && x <= 11 && !(x < 7 + notch)
      if ((inLeft || inRight) && !(y < 14 && Math.hypot(x - 6.5, y - 6.5) <= 6.6)) filled.add(`${x},${y}`)
    }
  }
  const has = (x, y) => filled.has(`${x},${y}`)
  for (const k of filled) {
    const [x, y] = k.split(',').map(Number)
    const edge = !has(x + 1, y) || !has(x - 1, y) || !has(x, y + 1) || !has(x, y - 1)
    const d = Math.hypot(x - 6.5, y - 6.5)
    let c = edge ? t.edge : y > 13 ? t.fill : d <= 1.6 ? '#ffffff' : d <= 4.2 ? t.hi : t.fill
    if (!edge && y > 13 && props.tier !== 'unclaimed' && x > 6) c = t.fill
    out.push({ x, y, c })
  }
  return out
})
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" :width="size" :height="size * H / W" shape-rendering="crispEdges" :class="['rb', tier]" role="img" :aria-label="`${tier} ribbon`">
    <rect v-for="c in cells" :key="c.x + ',' + c.y" :x="c.x" :y="c.y" width="1" height="1" :fill="c.c" />
  </svg>
</template>

<style scoped>
.rb { display:inline-block; vertical-align:middle; flex:none } .rb.unclaimed { opacity:.55 }
</style>
