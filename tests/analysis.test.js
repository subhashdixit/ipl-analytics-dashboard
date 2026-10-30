import test from 'node:test';
import assert from 'node:assert/strict';
import {selectMatches, selectedStats, totals, tossAssociation, playerLeaders} from '../site/lib.js';
const matches = [{id:'a',season:2020,teams:['A','B'],winner:'A',toss_winner:'A'}, {id:'b',season:2019,teams:['B','C'],winner:null,toss_winner:'B'}, {id:'c',season:2020,teams:['A','C'],winner:'C',toss_winner:'A'}];
test('season and team filters form the intended cohort', () => { assert.equal(selectMatches(matches,'2020','A').length,2); assert.equal(selectMatches(matches,'2019','A').length,0); });
test('no-results are excluded from the toss denominator', () => { assert.deepEqual(tossAssociation(matches),{decided:2,same:1,percentage:50}); assert.equal(tossAssociation([]).percentage,null); });
test('player rows must belong to both the selected match and team', () => { const rows=[{match_id:'a',team:'A'},{match_id:'a',team:'B'},{match_id:'b',team:'A'}]; assert.equal(selectedStats(rows,[matches[0]],'A').length,1); });
test('registry IDs combine aliases without merging different people', () => { const rows=[{player_id:'id1',player:'Name A',runs:10},{player_id:'id1',player:'Alias A',runs:20},{player_id:'id2',player:'Name A',runs:5}]; const leaders=playerLeaders(rows,'runs'); assert.equal(leaders[0].value,30); assert.equal(leaders.length,2); });
test('aggregation respects the requested measure and deterministic order', () => { assert.deepEqual(totals([{team:'A',runs:2},{team:'A',runs:3},{team:'B',runs:1}],'team','runs'),[{label:'A',value:5},{label:'B',value:1}]); });
