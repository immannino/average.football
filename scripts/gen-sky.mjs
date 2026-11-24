// Generates the dithered "sky" bitmaps for the Pixel theme (typesafe.ai look): fractal value noise run through a
// color ramp, per-pixel grain, then a stochastic dissolve to white. Deterministic (seeded), no dependencies.
//   node scripts/gen-sky.mjs
// Each entry in SKIES is just a ramp, so extra vibrant variants are one more entry.
import { mkdirSync, writeFileSync } from 'node:fs'
import { png, ramp, rng, seedOf } from './lib/texture.mjs'

const OUT = new URL('../public/textures/', import.meta.url)

const SKIES = [
  {
    file: 'pixel-sky.png',
    seed: 'pixel-sky',
    // blue base -> violet -> hot pink -> pale pink, sampled from typesafe.ai
    stops: [[0, '#4f9fd0'], [0.3, '#6fb0d8'], [0.5, '#9b6bff'], [0.68, '#f050c8'], [0.86, '#ff7bd8'], [1, '#ffd6f2']],
  },
  // One tint per color gauntlet, used behind that gauntlet's page: base -> mid -> bright -> pale.
  ...Object.entries({
    green: ['#2f8f5b', '#4fb37a', '#8fe08a', '#f2d84a', '#e8ffd0'],
    orange: ['#d9591e', '#f08a24', '#ffb347', '#ff8fa3', '#ffe6cc'],
    purple: ['#4b2e8f', '#7a4fd0', '#b06bff', '#f050c8', '#f4d6ff'],
    red: ['#a31d2b', '#d93a3a', '#ff6b4a', '#ffa94d', '#ffe0d6'],
    blue: ['#1f4fb0', '#3a82e0', '#5ec4f0', '#9b8cff', '#dcefff'],
  }).map(([name, c]) => ({ file: `pixel-sky-${name}.png`, seed: `sky-${name}`, stops: c.map((hex, i) => [i / 4, hex]) })),
]
const W = 640
const H = 300
const FADE = [0.4, 0.97] // dissolve to white between these fractions of the height

function skyImage({ seed, stops }) {
  const rand = rng(seedOf(seed))
  const N = 37
  const lat = new Float32Array(N * N).map(() => rand())
  const at = (a, b) => lat[(((b % N) + N) % N) * N + (((a % N) + N) % N)]
  const s = (t) => t * t * (3 - 2 * t)
  const vnoise = (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi
    const top = at(xi, yi) + (at(xi + 1, yi) - at(xi, yi)) * s(xf)
    const bot = at(xi, yi + 1) + (at(xi + 1, yi + 1) - at(xi, yi + 1)) * s(xf)
    return top + (bot - top) * s(yf)
  }
  const fbm = (x, y) => {
    let v = 0, a = 0.5, f = 1
    for (let o = 0; o < 5; o++) { v += a * vnoise(x * f, y * f); a /= 2; f *= 2 }
    return v / 0.97
  }
  const raw = Buffer.alloc((W * 3 + 1) * H)
  for (let y = 0; y < H; y++) {
    raw[y * (W * 3 + 1)] = 0
    for (let x = 0; x < W; x++) {
      // clouds get pinker toward the bottom, like the original
      const n = Math.min(1, Math.max(0, (fbm(x / 70, y / 55) - 0.3) * 1.7 + 0.12 * (y / H)))
      const grain = (rand() - 0.5) * 0.12
      let c = ramp(stops, Math.min(1, Math.max(0, n + grain)))
      const t = Math.min(1, Math.max(0, (y / H - FADE[0]) / (FADE[1] - FADE[0])))
      if (rand() < t * t * (3 - 2 * t)) c = [255, 255, 255]
      c.forEach((v, j) => (raw[y * (W * 3 + 1) + 1 + x * 3 + j] = Math.round(v)))
    }
  }
  return png(W, H, raw)
}

mkdirSync(OUT, { recursive: true })
for (const sky of SKIES) {
  writeFileSync(new URL(sky.file, OUT), skyImage(sky))
  console.log('wrote', sky.file)
}
