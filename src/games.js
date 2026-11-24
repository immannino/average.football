// Game-level data (~870 KB), fetched once and shared.
let p
export const loadGames = () => (p ??= fetch(`${import.meta.env.BASE_URL}data/games.json`).then((r) => r.json()))

const fmt = (iso) => new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'America/New_York' })

// One team's games in a season, from that team's point of view.
export function teamGames(games, team, season) {
  return (games || [])
    .filter((g) => g.season === season && (g.home === team || g.away === team))
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((g) => {
      const home = g.home === team
      const pf = home ? g.home_score : g.away_score, pa = home ? g.away_score : g.home_score
      return { opp: home ? g.away : g.home, at: home ? 'home' : 'away', date: fmt(g.date), iso: g.date, post: g.type === 'post',
        res: !g.completed ? 'next' : pf > pa ? 'W' : pf < pa ? 'L' : 'T', score: g.completed ? `${pf}-${pa}` : '' }
    })
}

// One line per required opponent, ordered by when the deciding / upcoming game is played.
export function opponentRows(gs, opps) {
  return opps.map((o) => {
    const mine = gs.filter((g) => g.opp === o)
    const win = mine.find((g) => g.res === 'W'), next = mine.find((g) => g.res === 'next')
    const key = win || next || mine.at(-1)
    return { o, gs: mine, next, state: win ? 'beaten' : next ? 'next' : mine.length ? 'lost' : 'none', ts: key?.iso || '9' }
  }).sort((a, b) => a.ts.localeCompare(b.ts))
}
