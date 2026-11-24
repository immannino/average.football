// Renders the share cards (public/data/digest.json events + a watch card) to out/cards/*.png using headless Chrome.
//   npm run cards            (builds the site first)   CHROME=/path/to/chrome to override the browser
import { spawn, execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync } from 'node:fs'

const PORT = 4180
const MAX = Number(process.env.MAX_CARDS || 12)
const candidates = [process.env.CHROME, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium'].filter(Boolean)
const chrome = candidates.find((c) => !c.includes('/') || existsSync(c))
if (!chrome) throw new Error('No Chrome found; set CHROME=/path/to/chrome')

const digest = JSON.parse(readFileSync(new URL('../public/data/digest.json', import.meta.url)))
const ids = ['watch', ...digest.events.slice(0, MAX).map((_, i) => `e${i}`)]
mkdirSync('out/cards', { recursive: true })

const server = spawn('npx', ['vite', 'preview', '--port', String(PORT), '--strictPort'], { stdio: 'ignore' })
const up = async () => { for (let i = 0; i < 50; i++) { try { await fetch(`http://localhost:${PORT}/`); return } catch { await new Promise((r) => setTimeout(r, 200)) } } throw new Error('preview did not start') }
try {
  await up()
  for (const id of ids) {
    const file = id === 'watch' ? 'watch' : `${id}-${digest.events[Number(id.slice(1))].kind}-${digest.events[Number(id.slice(1))].team}-${digest.events[Number(id.slice(1))].gauntlet}`
    execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--virtual-time-budget=15000', '--window-size=1080,1350',
      `--screenshot=out/cards/${file}.png`, `http://localhost:${PORT}/#card=${id}`], { stdio: 'ignore' })
    console.log('wrote', `out/cards/${file}.png`)
  }
} finally { server.kill() }
