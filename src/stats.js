// Tier by how rarely qualifying teams finish a gauntlet (rate = completions / qualifying team-seasons, finished seasons only).
export const TIERS = {
  unclaimed: { label: 'Unclaimed', fill: '#ffffff', hi: '#ffffff', edge: '#9a9a9a' },
  bronze: { label: 'Bronze', fill: '#b87333', hi: '#e0a070', edge: '#1e1e1e' },
  silver: { label: 'Silver', fill: '#aeb4bc', hi: '#eceff2', edge: '#1e1e1e' },
  gold: { label: 'Gold', fill: '#f2c200', hi: '#ffe777', edge: '#1e1e1e' },
  legendary: { label: 'Legendary', fill: '#c4259c', hi: '#ff8be0', edge: '#1e1e1e' },
}
export const tierOf = (r) => (!r || r.done === 0 ? 'unclaimed' : r.rate < 0.05 ? 'legendary' : r.rate < 0.25 ? 'gold' : r.rate < 0.4 ? 'silver' : 'bronze')
export const tierNote = 'Legendary: under 5% of attempts finish it. Gold: under 25%. Silver: under 40%. Bronze: the rest. Unclaimed: nobody has since 2002.'
