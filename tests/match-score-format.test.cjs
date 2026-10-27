const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'tivvy-hub-preview.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
for (const script of scripts) new vm.Script(script);
const source = scripts.find(s => s.includes('function matchScore('));
const prefix = source.slice(0, source.indexOf('function kickoffTime('));
const sharing = source.slice(source.indexOf('function matchShareText('), source.indexOf('function sharingMarkup('));
const context = vm.createContext({URLSearchParams});
vm.runInContext(prefix + sharing, context);
const load = name => JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
const fixtures = load('match-centre-fixtures-2026-27.json').fixtures;
const details = [
  ...load('data.json').fixtures.map(f => ({...f, competition:'SLD1S'})),
  ...load('cup-match-details-2026-27.json').fixtures,
  ...load('historical-match-details-2026-27.json').fixtures,
];
context.inputDetails = details;
vm.runInContext('details=inputDetails;', context);

test('Shaftesbury and Falmouth display home-first with only Tiverton goals red', () => {
  const shaftesbury = fixtures.find(f => f.date === '2026-10-10');
  const falmouth = fixtures.find(f => f.date === '2026-10-13');
  assert.equal(context.result(shaftesbury), 'W 1–<span class="tivvy">4</span>');
  assert.equal(context.result(falmouth), 'L 2–<span class="tivvy">1</span>');
  assert.match(context.matchShareText(shaftesbury), /^Shaftesbury 1–4 Tiverton Town/);
  assert.match(context.matchShareText(falmouth), /^Falmouth Town 2–1 Tiverton Town/);
});

test('both legacy CMS score orders resolve consistently, including games without detail', () => {
  for (const venue of ['H','A']) for (const result of ['W 1-4','W 4-1','w 1–4']) {
    const f = {date:'2026-01-01', opposition:'Fallback', competition:'PSF', homeAway:venue, result};
    assert.equal(context.result(f), venue === 'A' ? 'W 1–<span class="tivvy">4</span>' : 'W <span class="tivvy">4</span>–1');
  }
  for (const result of ['L 1-2','L 2-1']) {
    assert.equal(context.result({date:'2026-01-01', opposition:'Fallback', homeAway:'A', result}), 'L 2–<span class="tivvy">1</span>');
  }
  assert.equal(context.result({result:'P-P'}), 'P-P');
  assert.equal(context.result({result:''}), '—');
});

test('every completed season fixture agrees with verified scores and red team ownership', () => {
  const played = fixtures.filter(f => /^(W|D|L|ABD)\s+\d+\s*[-–]\s*\d+$/i.test(f.result));
  assert(played.length >= 28, 'Audit must cover pre-season, cup and league games');
  for (const fixture of played) {
    const score = context.matchScore(fixture);
    const detail = context.matchFor(fixture);
    assert(detail, `${fixture.date} ${fixture.opposition}: missing verification record`);
    const [gf,ga] = detail.result.split(/[-–]/).map(Number);
    assert.equal(score.tivGoals,gf,fixture.opposition);
    assert.equal(score.oppGoals,ga,fixture.opposition);
    const expected = fixture.homeAway === 'A' ? `${ga}–<span class="tivvy">${gf}</span>` : `<span class="tivvy">${gf}</span>–${ga}`;
    assert.equal(context.result(fixture), `${score.outcome} ${expected}`,fixture.opposition);
    if (score.outcome !== 'ABD') assert.equal(score.outcome, fixture.result[0].toUpperCase(),fixture.opposition);
    // Both desktop and mobile fixture rows use the identical formatted score.
    assert.equal(context.row(fixture).split(context.result(fixture)).length-1,2,fixture.opposition);
  }
});
