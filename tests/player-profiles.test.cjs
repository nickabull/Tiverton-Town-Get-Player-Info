const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const vm = require('node:vm');
const root = join(__dirname, '..');
const html = readFileSync(join(root,'stats-centre.html'),'utf8');
const source = readFileSync(join(root,'player-profiles.js'),'utf8');
const helpers = html.slice(html.indexOf('const parseScore='),html.indexOf('const reports='));
const original = html.slice(html.indexOf('function buildPlayerStats('),html.indexOf('function matrixAxisLabel('));
const context = {}; vm.createContext(context);
vm.runInContext(helpers + original + source.split('(function () {')[0] + ';this.build=buildPlayerProfiles;this.previous=buildPlayerStats;',context);
const fixtures = JSON.parse(readFileSync(join(root,'data.json'))).fixtures;
const profiles = context.build(fixtures), previous = context.previous(fixtures).stats;
for (const profile of profiles) {
  const old = previous.find(p=>p.name===profile.name);
  for (const key of ['apps','starts','subs','mins','goals','caps']) assert.equal(profile[key],old[key],profile.name+' '+key);
}
const bissett=profiles.find(p=>p.name==='Josh Bissett');
assert.equal(bissett.goals,5);assert.equal(bissett.penaltyGoals,1);assert.equal(bissett.matches.find(m=>m.date==='2026-10-24').goals,3);
const dorchester=fixtures.find(f=>f.date==='2026-10-27');
assert.equal(dorchester.result,'2-2');
assert.equal(profiles.find(p=>p.name==='Louis Jagger Cane').matches.find(m=>m.date==='2026-10-27').goals,1);
assert.equal(profiles.find(p=>p.name==='Owen Howe').matches.find(m=>m.date==='2026-10-27').goals,1);
assert.equal(profiles.find(p=>p.name==='Corey Koerner').matches.find(m=>m.date==='2026-10-27').used,false);
assert.equal(profiles.filter(p=>/Slough/.test(p.name)).length,1);
const edge=context.build([{date:'2026-10-24',opponent:'Test',venue:'H',result:'2-0',
  starterDetails:[{name:'Louis Slough',goalCount:1,goalMinutes:['45+3'],captain:true}],
  subDetails:[{name:'Finisher',used:true,onMinute:'90',goalCount:1,goalMinutes:['90+2'],penaltyMinutes:['90+2']},{name:'Unused',used:false}],
  penalties:[{player:'Finisher',minute:'90+2',outcome:'scored'}]}]);
const finisher=edge.find(p=>p.name==='Finisher'),unused=edge.find(p=>p.name==='Unused'),slough=edge.find(p=>p.name==='Louie Slough');
assert.equal(slough.goalBands[2],1);assert.equal(finisher.goalBands[5],1);assert.equal(finisher.mins,2);
assert.equal(finisher.penaltyGoals,1,'duplicate penalty metadata counted once');
assert.equal(unused.apps,0);assert.equal(unused.unused,1);assert.equal(unused.matches[0].used,false);
assert.equal(slough.homeGoals,1);assert.equal(slough.caps,1);
assert.equal(context.build([{date:'2026-11-01',result:'',starterDetails:[{name:'Future'}]}]).length,0);
console.log('Player profiles: all existing totals agree; aliases, substitutes, stoppage time, penalties and future fixtures pass.');
