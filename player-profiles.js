/* Individual profiles use the same league team sheets as the Player Centre. */
const playerName = value => String(value || '').trim().replace(/^Louis Slough$/i, 'Louie Slough');
const playerKey = value => playerName(value).toLocaleLowerCase('en-GB');

function buildPlayerProfiles(fixtures) {
  const profiles = new Map();
  const get = name => {
    name = playerName(name);
    if (!profiles.has(playerKey(name))) profiles.set(playerKey(name), {
      name, apps: 0, starts: 0, subs: 0, mins: 0, goals: 0, caps: 0, unused: 0,
      homeGoals: 0, awayGoals: 0, penaltyGoals: 0, timedGoals: 0,
      goalBands: [0, 0, 0, 0, 0, 0], matches: []
    });
    return profiles.get(playerKey(name));
  };
  const number = value => Math.max(0, Number(value) || 0);
  fixtures.filter(f => parseScore(f.result) && f.date).slice().sort((a, b) => a.date.localeCompare(b.date)).forEach(f => {
    const starters = f.starterDetails || [], subs = f.subDetails || [];
    const events = [...starters, ...subs].flatMap(p => [p.onMinute, p.offMinute, ...(p.goalMinutes || [])]).map(minute).filter(Number.isFinite);
    const end = Math.max(90, ...events);
    const score = parseScore(f.result), outcome = score.gf > score.ga ? 'W' : score.gf === score.ga ? 'D' : 'L';
    const seen = new Set();
    for (const [isStart, players] of [[true, starters], [false, subs]]) {
      for (const p of players) {
        if (!p.name || seen.has(playerKey(p.name))) continue;
        seen.add(playerKey(p.name));
        const profile = get(p.name), used = isStart || (p.used !== false && (Boolean(p.onMinute) || p.used === true));
        const on = minute(p.onMinute), off = minute(p.offMinute);
        const mins = used ? Math.max(0, (Number.isFinite(off) ? Math.min(off, end) : end) - (isStart ? 0 : (Number.isFinite(on) ? on : end))) : 0;
        const goals = used ? number(p.goalCount) : 0;
        const penaltyMinutes = new Set((p.penaltyMinutes || []).map(String));
        for (const pen of f.penalties || []) {
          if (playerKey(pen.player) === playerKey(p.name) && pen.outcome === 'scored') penaltyMinutes.add(String(pen.minute));
        }
        const penalties = Math.min(goals, penaltyMinutes.size);
        if (used) {
          profile.apps++; profile[isStart ? 'starts' : 'subs']++; profile.mins += mins;
          profile.goals += goals; profile.caps += p.captain ? 1 : 0;
          profile[f.venue === 'H' ? 'homeGoals' : 'awayGoals'] += goals;
          profile.penaltyGoals += penalties;
          for (const time of (p.goalMinutes || []).slice(0, goals)) {
            const n = minute(time);
            if (Number.isFinite(n)) {
              const base = Number(String(time).split('+')[0]);
              const band = base <= 45 ? Math.min(2, Math.max(0, Math.ceil(base / 15) - 1)) : Math.min(5, Math.ceil(base / 15) - 1);
              profile.goalBands[band]++; profile.timedGoals++;
            }
          }
        } else profile.unused++;
        profile.matches.push({date: f.date, opponent: f.opponent, venue: f.venue, result: f.result,
          outcome, start: isStart, used, mins, goals, penalties, captain: Boolean(p.captain),
          onMinute: p.onMinute || '', offMinute: p.offMinute || '', goalMinutes: p.goalMinutes || [],
          report: f.officialReportUrl || '', crest: f.opponentLogoUrl || ''});
      }
    }
  });
  return [...profiles.values()].sort((a, b) => a.name.localeCompare(b.name));
}

(function () {
  let profiles = [], current = '', pending = new URLSearchParams(location.search).get('player') || '';
  const host = document.getElementById('playerProfile');
  if (!host) return;
  const node = id => document.getElementById(id);
  const embedded = window.parent !== window;
  const message = data => { if (embedded) window.parent.postMessage(data, location.origin); };
  const find = name => profiles.find(p => playerKey(p.name) === playerKey(name));
  const stat = (value, label, red = false) => '<div class="profile-stat"><strong' + (red ? ' class="profile-goals"' : '') + '>' + esc(value) + '</strong><span>' + esc(label) + '</span></div>';
  const nameButton = name => '<button type="button" class="player-name-link" data-player-name="' + esc(name) + '">' + esc(name) + '</button>';
  window.playerProfileNameButton = nameButton;
  function setURL(name) {
    const url = new URL(location.href);
    if (name) url.searchParams.set('player', name); else url.searchParams.delete('player');
    history.replaceState(null, '', url);
    message({type: 'tivvy-player-selected', name: name || ''});
  }
  function matchURL(m) {
    const url = new URL('tivvy-hub-preview.html', location.href);
    url.searchParams.set('fixtureDate', m.date); url.searchParams.set('opponent', m.opponent);
    url.searchParams.set('venue', m.venue); url.hash = 'fixtures'; return url.href;
  }
  function matchCard(m, compact) {
    const status = m.used ? (m.start ? 'Started' : 'Sub on' + (m.onMinute ? " " + m.onMinute + "′" : '')) + (m.offMinute ? ' · Off ' + m.offMinute + '′' : '') : 'Unused substitute';
    const score = parseScore(m.result);
    const img = crestUrl(m.opponent) || m.crest;
    return '<a class="profile-match' + (compact ? ' compact' : '') + '" href="' + esc(matchURL(m)) + '" data-profile-match="' + esc(JSON.stringify({date:m.date,opponent:m.opponent,venue:m.venue})) + '">' +
      '<span class="profile-result result-' + m.outcome.toLowerCase() + '">' + m.outcome + '</span>' +
      '<span class="profile-match-main"><span class="profile-opponent">' + (img && /^https:\/\//.test(img) ? '<img src="' + esc(img) + '" alt="" loading="lazy" onerror="this.remove()">' : '') + esc(m.opponent) + ' <small>' + (m.venue === 'H' ? 'HOME' : 'AWAY') + '</small></span>' +
      '<span class="profile-match-meta">' + esc(fmt(m.date)) + ' · ' + esc(status) + (m.used ? ' · ≈' + m.mins + ' min' : '') + (m.captain ? ' · Captain' : '') + '</span>' +
      (m.goals ? '<span class="profile-match-goals">⚽ ' + m.goals + (m.goalMinutes.length ? ' · ' + esc(m.goalMinutes.join('′, ') + '′') : '') + (m.penalties ? ' · ' + m.penalties + ' pen' : '') + '</span>' : '') +
      '</span><span class="profile-score">' + (m.venue === 'A' ? score.ga + '–<b>' + score.gf + '</b>' : '<b>' + score.gf + '</b>–' + score.ga) + '<span>DETAILS ↗</span></span></a>';
  }
  function compare() {
    const p = find(current), other = find(node('profileCompareSelect').value), target = node('profileComparison');
    if (!p || !other) { target.innerHTML = '<p class="profile-note">Choose a teammate to compare their league season.</p>'; return; }
    const rows = [['Appearances','apps'],['Starts','starts'],['Sub appearances','subs'],['Estimated minutes','mins'],['Goals','goals'],['Captaincies','caps']];
    target.innerHTML = '<table class="profile-compare-table"><thead><tr><th scope="col">Statistic</th><th scope="col">' + esc(p.name) + '</th><th scope="col">' + esc(other.name) + '</th></tr></thead><tbody>' + rows.map(([label,key]) => '<tr><th scope="row">' + label + '</th><td' + (key === 'goals' ? ' class="profile-goals"' : '') + '>' + p[key] + '</td><td' + (key === 'goals' ? ' class="profile-goals"' : '') + '>' + other[key] + '</td></tr>').join('') + '</tbody></table>';
  }
  function show(name, focus = true) {
    if (!profiles.length) { pending = name; return; }
    const p = find(name) || {name:playerName(name),apps:0,starts:0,subs:0,mins:0,goals:0,caps:0,unused:0,homeGoals:0,awayGoals:0,penaltyGoals:0,timedGoals:0,goalBands:[0,0,0,0,0,0],matches:[]};
    current = p.name; pending = ''; const oldCompare = node('profileCompareSelect')?.value || '';
    const appearances = p.matches.filter(m => m.used), latest = appearances.slice(-5).reverse();
    const labels = ['1–15','16–30','31–45+','46–60','61–75','76–90+'], max = Math.max(1,...p.goalBands);
    host.innerHTML = '<div class="profile-toolbar"><button type="button" class="profile-back" id="profileBack">← ALL PLAYERS</button><label class="profile-switch-label">PLAYER<select id="profilePlayerSelect" aria-label="Choose player profile">' + (find(p.name)?profiles:[p,...profiles]).map(x=>'<option'+(x.name===p.name?' selected':'')+'>'+esc(x.name)+'</option>').join('') + '</select></label></div>' +
      '<div class="profile-hero"><div><p>YOUR TIVVY · PLAYER PROFILE</p><h3 id="profileName" tabindex="-1">' + esc(p.name) + '</h3><span>2026/27 · SOUTHERN LEAGUE DIVISION ONE SOUTH</span></div>' + crestImg('Tiverton Town','profile-club-crest') + '</div>' +
      '<div class="profile-stats">' + stat(p.apps,'Appearances') + stat(p.starts,'Starts') + stat(p.subs,'Sub on') + stat(p.mins,'Est. minutes') + stat(p.goals,'Goals',true) + stat(p.caps,'Captaincies') + '</div>' +
      '<p class="profile-note">Recorded league team sheets only. Minutes are estimates. Unused substitute: ' + p.unused + ' match' + (p.unused===1?'':'es') + '.</p>' +
      '<div class="profile-grid"><section class="profile-panel"><h4>THE GOAL BREAKDOWN</h4><div class="profile-goal-split">' + stat(p.homeGoals,'At home',true) + stat(p.awayGoals,'Away',true) + '</div><p class="profile-note">' + p.penaltyGoals + ' penalty goal' + (p.penaltyGoals===1?'':'s') + ' explicitly recorded · ' + (p.goals-p.penaltyGoals) + ' other / unclassified goals.</p><div class="profile-goal-bands">' + labels.map((label,i)=>'<div class="profile-goal-band"><span>'+label+'′</span><span class="profile-bar"><i style="width:'+(100*p.goalBands[i]/max)+'%"></i></span><strong>'+p.goalBands[i]+'</strong></div>').join('') + '</div><p class="profile-note">' + (p.goals ? p.timedGoals + ' of ' + p.goals + ' goals have a recorded minute. Stoppage time stays with its half.' : 'No league goals recorded yet.') + '</p></section>' +
      '<section class="profile-panel"><h4>LAST FIVE APPEARANCES</h4><p class="profile-note">Latest first · W/D/L is the team result.</p><div>' + (latest.map(m=>matchCard(m,true)).join('') || '<p class="profile-note">No recorded league appearances yet.</p>') + '</div></section></div>' +
      '<section class="profile-panel profile-compare"><h4>HEAD TO HEAD</h4><div class="profile-compare-control"><label for="profileCompareSelect">Compare ' + esc(p.name) + ' with</label><select id="profileCompareSelect"><option value="">Choose a teammate…</option>' + profiles.filter(x=>x.name!==p.name).map(x=>'<option'+(x.name===oldCompare?' selected':'')+'>'+esc(x.name)+'</option>').join('') + '</select></div><div id="profileComparison"></div></section>' +
      '<section class="profile-panel profile-history"><h4>THE SEASON, MATCH BY MATCH</h4><p class="profile-note">Tap a match for its line-up, report and available photos.</p>' + (p.matches.slice().reverse().map(m=>matchCard(m,false)).join('') || '<p class="profile-note">No league team-sheet records available for this player.</p>') + '</section>';
    host.hidden = false; document.getElementById('players').classList.add('profile-active');
    node('profileBack').onclick = close; node('profilePlayerSelect').onchange = e => show(e.target.value);
    node('profileCompareSelect').onchange = compare; compare(); setURL(p.name);
    if (focus) { node('profileName').focus({preventScroll:true}); if (!embedded) host.scrollIntoView({block:'start'}); }
    message({type:'tivvy-player-resize'});
  }
  function close() {
    host.hidden = true; document.getElementById('players').classList.remove('profile-active');
    const previous = current; current = ''; setURL('');
    const source = [...document.querySelectorAll('[data-player-name]')].find(el=>el.dataset.playerName===previous);
    source?.focus({preventScroll:true}); message({type:'tivvy-player-resize'});
  }
  document.getElementById('players').addEventListener('click', event => {
    const button = event.target.closest('[data-player-name]');
    if (button) { show(button.dataset.playerName); return; }
    const match = event.target.closest('[data-profile-match]');
    if (match && embedded) { event.preventDefault(); message({type:'tivvy-match-open',...JSON.parse(match.dataset.profileMatch)}); }
  });
  window.addEventListener('message', event => {
    if (event.origin !== location.origin || event.source !== window.parent) return;
    if (event.data?.type === 'tivvy-player-open' && typeof event.data.name === 'string') show(event.data.name);
  });
  window.initialisePlayerProfiles = fixtures => {
    profiles = buildPlayerProfiles(fixtures);
    if (pending) show(pending,false);
    message({type:'tivvy-player-ready'});
  };
})();
