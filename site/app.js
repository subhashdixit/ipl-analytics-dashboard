import {barChart, lineChart, metric, number, table, downloadCsv, element} from './charts.js';
import {selectMatches, selectedStats, totals, tossAssociation, playerLeaders} from './lib.js';
const get = id => document.getElementById(id);
let data, exported = [];
function addOptions(select, rows) {
  for (const [value, label] of rows) { const option = element('option', label); option.value = value; select.append(option); }
}
function render() {
  const matches = selectMatches(data.matches, get('season').value, get('team').value);
  const stats = selectedStats(data.players, matches, get('team').value);
  const names = new Map(stats.map(row => [row.player_id, row.player]));
  const oldPlayer = get('player').value;
  get('player').replaceChildren(); addOptions(get('player'), [['all', 'All players'], ...[...names].sort((a, b) => a[1].localeCompare(b[1]))]);
  get('player').value = names.has(oldPlayer) ? oldPlayer : 'all';
  const toss = tossAssociation(matches);
  get('metrics').replaceChildren(metric('Matches', number(matches.length)), metric('Players', number(names.size)), metric('Regulation runs', number(matches.reduce((sum, row) => sum + row.runs, 0))), metric('Toss winner also won', toss.percentage === null ? 'Unavailable' : number(toss.percentage, 1) + '%', `${toss.decided} decided matches`));
  barChart(get('wins'), totals(matches.filter(row => row.winner), 'winner').slice(0, 10), 'Wins in selected matches');
  barChart(get('venues'), totals(matches, 'venue').slice(0, 10), 'Matches by venue');
  barChart(get('batting'), playerLeaders(stats, 'runs').slice(0, 10), 'Top batting runs');
  barChart(get('bowling'), playerLeaders(stats, 'wickets').slice(0, 10), 'Top bowler wickets');
  const selected = get('player').value;
  const playerStats = selected === 'all' ? stats : stats.filter(row => row.player_id === selected);
  const trend = totals(playerStats, 'season', 'runs').sort((a, b) => Number(a.label) - Number(b.label));
  lineChart(get('trend'), trend, 'Runs by season');
  get('player-note').textContent = selected === 'all' ? 'All selected players combined. Choose a player for an individual trend.' : names.get(selected);
  const grouped = new Map();
  for (const row of stats) {
    if (!grouped.has(row.player_id)) grouped.set(row.player_id, {name: row.player, matches: new Set(), runs: 0, balls: 0, wickets: 0});
    const item = grouped.get(row.player_id); item.matches.add(row.match_id); item.runs += row.runs; item.balls += row.balls_faced; item.wickets += row.wickets;
  }
  exported = [...grouped.values()].sort((a, b) => b.runs - a.runs).map(row => [row.name, row.matches.size, row.runs, row.balls, row.balls ? (row.runs / row.balls * 100).toFixed(2) : 'Undefined', row.wickets]);
  table(get('player-table'), ['Player', 'Matches', 'Runs', 'Balls faced', 'Strike rate', 'Bowler wickets'], exported);
}
async function start() {
  try {
    const response = await fetch('./data.json'); if (!response.ok) throw new Error('Cannot load prepared data.');
    data = await response.json();
    addOptions(get('season'), [...new Set(data.matches.map(row => row.season))].sort((a, b) => a - b).map(year => [String(year), String(year)]));
    addOptions(get('team'), [...new Set(data.matches.flatMap(row => row.teams))].sort().map(team => [team, team]));
    for (const id of ['season', 'team', 'player']) get(id).addEventListener('change', render);
    get('download').addEventListener('click', () => downloadCsv('ipl-player-summary.csv', ['player', 'matches', 'runs', 'balls_faced', 'strike_rate', 'bowler_wickets'], exported));
    get('provenance').textContent = `${data.manifest.selected_matches} available matches, ${data.manifest.first_date} to ${data.manifest.last_date}. ${data.manifest.super_over_innings_excluded} super-over innings excluded from player totals.`;
    get('status').textContent = 'Prepared source aggregates loaded. Filters run in your browser.';
    render();
  } catch (error) { get('error').hidden = false; get('error').textContent = error.message; get('status').textContent = 'Data could not be loaded.'; }
}
start();
