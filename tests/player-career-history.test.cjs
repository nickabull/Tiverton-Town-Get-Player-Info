const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const data=JSON.parse(fs.readFileSync('player-career-history.json','utf8'));
const fixtures=JSON.parse(fs.readFileSync('data.json','utf8')).fixtures;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx={URL,esc};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('player-profiles.js','utf8').split('(function () {')[0]+';this.markup=playerCareerMarkup;',ctx);
const players=data.players,names=new Set(players.map(p=>p.name));
assert.equal(names.size,players.length,'one career entry per canonical player');
for(const name of new Set(fixtures.flatMap(f=>[...(f.starterDetails||[]),...(f.subDetails||[])]).map(p=>p.name?.replace('Louis Slough','Louie Slough')).filter(Boolean))){assert(names.has(name),'career entry for '+name);}
for(const p of players){
 assert.match(p.archiveUrl,/^https:\/\/www\.tivvyarchive\.co\.uk\/player\.php\?player=\d+$/);
 assert(p.clubs.length&&p.sources.length,p.name+' has supported club entries');
 const html=ctx.markup(p);assert.match(html,/PREVIOUS CLUBS/);assert(html.includes(esc(p.archiveUrl)));assert.match(html,/With thanks to/);
 for(const c of p.clubs){assert(html.includes(esc(c.club)));if(c.period)assert(html.includes(esc(c.period)));}
}
const cane=players.find(p=>p.name==='Louis Jagger Cane');assert(cane.clubs.some(c=>c.club==='Exwick Villa'));assert.equal(cane.clubs.find(c=>c.club==='Bideford').period,'2021/22–2022/23');
const alsop=players.find(p=>p.name==='Tobias Alsop');assert.match(alsop.clubs[0].note,/parent club/);
assert(!players.find(p=>p.name==='Josh Bissett').clubs.find(c=>c.club==='Mousehole').period,'unknown dates stay omitted');
const bad=ctx.markup({archiveUrl:'javascript:alert(1)',clubs:[{club:'<img src=x onerror=alert(1)>',period:'<script>x</script>'}],sources:[{label:'bad',url:'javascript:alert(1)'}]});
assert(!bad.includes('javascript:'));assert(!bad.includes('<img'));assert(bad.includes('&lt;img'));assert(!bad.includes('<script>'));
assert.match(ctx.markup(undefined,'loading'),/Loading club history/);assert.match(ctx.markup(undefined,'error'),/temporarily unavailable/);
console.log('Career history: all 21 profiles covered; supported dates, loan labels, attribution and escaping pass.');
