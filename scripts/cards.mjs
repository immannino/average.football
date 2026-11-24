// Renders share cards to out/cards/<size>/*.png with headless Chrome. Uses public/data/digest.json and the live-season data.
//   npm run cards                                  watch + events + carousel at 1080x1350
//   npm run cards -- --sizes post,story,square     also story (1080x1920) and square (1080x1080) versions
//   npm run cards -- --sizes og --only og         link preview -> public/og.png (committed; not part of the Instagram set)
//   npm run cards -- --only watch|events|carousel  just one kind;  --max 12 caps the number of event cards
// CHROME=/path/to/chrome overrides the browser.
import { spawn, execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync } from 'node:fs'

const arg = (name, dflt) => { const i = process.argv.indexOf(`--${name}`); return i > -1 ? process.argv[i + 1] : dflt }
const SIZES = { post: [1080, 1350], story: [1080, 1920], square: [1080, 1080], og: [1200, 630] }
const sizes = arg('sizes', 'post').split(',').map((s) => s.trim())
const only = arg('only', 'all')
const max = Number(arg('max', 12))
for (const s of sizes) if (!SIZES[s]) throw new Error(`unknown size ${s} (use ${Object.keys(SIZES).join(', ')})`)

const PORT = 4180
const candidates = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium'].filter(Boolean)
const chrome = candidates.find((c) => !c.includes('/') || existsSync(c))
if (!chrome) throw new Error('No Chrome found; set CHROME=/path/to/chrome')

const read = (f) => JSON.parse(readFileSync(new URL(`../public/data/${f}.json`, import.meta.url)))
const digest = read('digest')
const results = read('gauntlet_results')
const season = Math.max(...results.map((r) => r.season))
const live = new Set(results.filter((r) => r.season === season && r.status === 'in-progress').map((r) => r.gauntlet)).size
const slides = Math.min(8, live) + 2 // cover + one per live gauntlet + closer

const jobs = []
for (const size of sizes) {
  if (size === 'og') { if (only === 'all' || only === 'og') jobs.push({ size, id: 'og', file: 'og', dir: 'public' }); continue }
  if (only === 'all' || only === 'watch') jobs.push({ size, id: 'watch', file: 'watch' })
  if (only === 'all' || only === 'events')
    digest.events.slice(0, max).forEach((e, i) => jobs.push({ size, id: `e${i}`, file: `e${i}-${e.kind}-${e.team}-${e.gauntlet}` }))
  if (only === 'all' || only === 'carousel')
    for (let i = 0; i < slides; i++) jobs.push({ size, id: `c${i}`, file: `carousel-${String(i + 1).padStart(2, '0')}` })
}

const server = spawn('npx', ['vite', 'preview', '--port', String(PORT), '--strictPort'], { stdio: 'ignore' })
const up = async () => { for (let i = 0; i < 50; i++) { try { await fetch(`http://localhost:${PORT}/`); return } catch { await new Promise((r) => setTimeout(r, 200)) } } throw new Error('preview did not start') }
try {
  await up()
  for (const { size, id, file, dir: outDir } of jobs) {
    const dir = outDir || `out/cards/${size}`
    mkdirSync(dir, { recursive: true })
    const [w, h] = SIZES[size]
    execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=15000', `--window-size=${w},${h}`,
      `--screenshot=${dir}/${file}.png`, `http://localhost:${PORT}/#card=${id}@${size}`], { stdio: 'ignore' })
    console.log('wrote', `${dir}/${file}.png`)
  }
} finally { server.kill() }
