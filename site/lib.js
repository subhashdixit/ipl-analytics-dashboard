/** Pure analysis functions; no browser globals or remote APIs. */
export function selectMatches(matches, season = 'all', team = 'all') {
  return matches.filter(match => (season === 'all' || match.season === Number(season)) && (team === 'all' || match.teams.includes(team)));
}
export function selectedStats(players, matches, team = 'all') {
  const ids = new Set(matches.map(match => match.id));
  return players.filter(row => ids.has(row.match_id) && (team === 'all' || row.team === team));
}
export function totals(rows, key, value = null) {
  const grouped = new Map();
  for (const row of rows) {
    const id = row[key];
    grouped.set(id, (grouped.get(id) || 0) + (value ? row[value] : 1));
  }
  return [...grouped].map(([label, amount]) => ({label: String(label), value: amount})).sort((a, b) => b.value - a.value || a.label.localeCompare(b.label));
}
export function tossAssociation(matches) {
  const decided = matches.filter(match => match.winner);
  const same = decided.filter(match => match.winner === match.toss_winner).length;
  return {decided: decided.length, same, percentage: decided.length ? same / decided.length * 100 : null};
}
export function playerLeaders(stats, field) {
  const names = new Map(stats.map(row => [row.player_id, row.player]));
  return totals(stats, 'player_id', field).map(row => ({...row, id: row.label, label: names.get(row.label)}));
}
