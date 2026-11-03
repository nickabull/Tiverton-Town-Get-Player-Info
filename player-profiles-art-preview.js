
// Approved Tivvy artwork, sourced from the squad gallery preview (no re-created crests).
const tivvyCardPhotos={"aaron-wellington":"https://static.wixstatic.com/media/8aa829_341ebcb77e794cd2b0fe7534293a6c2d~mv2.png","aiden-horne":"https://static.wixstatic.com/media/8aa829_012f1fbb61014842b6a897ea8efb7446~mv2.png","asa-hall":"https://static.wixstatic.com/media/8aa829_37b4ea236d174d5a90824e7d396ee1f1~mv2.png","billy-tucker":"https://static.wixstatic.com/media/8aa829_72a3e03e9f8e49b29a83633bbb4bf11e~mv2.png","corey-koerner":"https://static.wixstatic.com/media/8aa829_b76b9523565343d99d3301c915aa4977~mv2.png","dan-koita":"https://static.wixstatic.com/media/8aa829_1f5a4cedd9e043dbae78b14dc7db3c9d~mv2.png","ed-palmer":"https://static.wixstatic.com/media/8aa829_1b54df80b2c94ae2a906bdf9851d15f8~mv2.png","finn-hodge":"https://static.wixstatic.com/media/8aa829_f4b68ebbbf01431daec2f0164f1f9430~mv2.png","finn-roberts":"https://static.wixstatic.com/media/8aa829_ae75aa2346974e80946c94cd679f3791~mv2.png","jack-kennell":"https://static.wixstatic.com/media/8aa829_e48c892b583f4b76b20703891c56ff4f~mv2.png","jacob-wellington":"https://static.wixstatic.com/media/8aa829_79191ea70db34e93897042ac05f18685~mv2.png","josh-bissett":"https://static.wixstatic.com/media/8aa829_3d1548970ffb40b5ae8b97b5b6fb193f~mv2.png","karim-coulibaly":"https://static.wixstatic.com/media/8aa829_256e163a46014a26beef49ef434ac967~mv2.png","louie-slough":"https://static.wixstatic.com/media/8aa829_6684a7b2e03c4b299c56ec07291bf83d~mv2.png","louis-jagger-cane":"https://static.wixstatic.com/media/8aa829_6e9c403d1b0b465ea12d55eab1ae2e88~mv2.png","louis-smith":"https://static.wixstatic.com/media/8aa829_b1be1b6074694a0ca185d115564c7e52~mv2.png","mason-winter":"https://static.wixstatic.com/media/8aa829_6fc4a5a9d42144d488e87046a3b34adb~mv2.png","matt-wood":"https://static.wixstatic.com/media/8aa829_8289ed63195e4553a0dfffd918ce04f0~mv2.png","owen-howe":"https://static.wixstatic.com/media/8aa829_e6b7e0879c31459c8705b8af6de9ce4b~mv2.png","ryan-keates":"https://static.wixstatic.com/media/8aa829_a93fe520111741d5998d0737ff3499d0~mv2.png","tobias-alsop":"https://static.wixstatic.com/media/8aa829_8cc51513e6744f85997af6914de5dcc8~mv2.png","toby-stephens":"https://static.wixstatic.com/media/8aa829_aee9bfe88b324647a64023f388be7c85~mv2.png"};
const tivvyCardPlacements={"finn-roberts":[-20,-5,100,0,0,0,0,0,-20,200,0],"jack-kennell":[-455,0,105,375,0,365,0,0,-20,200,0],"jacob-wellington":[-530,0,110,240,0,225,0,0,-20,200,0],"josh-bissett":[-445,0,140,385,0,370,0,0,-20,200,0],"karim-coulibaly":[-540,-5,100,275,0,265,0,0,-20,200,0],"lewis-flowers":[0,0,100,0,0,0,0,0,-20,115,0],"louie-slough":[-25,120,140,0,0,0,0,0,-20,200,0],"louis-jagger-cane":[-535,0,100,235,0,215,0,0,-20,200,0],"louis-smith":[-25,-5,100,0,0,0,0,25,-5,200,0],"mason-winter":[-495,0,130,350,0,330,0,0,-20,200,0],"matt-wood":[-520,90,130,445,0,430,0,0,-20,200,0],"owen-howe":[0,0,115,0,0,0,0,0,-20,200,0],"ryan-keates":[-35,55,135,0,0,0,0,0,-20,200,0],"tobias-alsop":[0,0,105,0,0,0,0,0,-20,200,0],"toby-stephens":[0,30,115,0,0,0,0,0,-20,200,0],"aaron-wellington":[10,0,115,0,0,0,0,0,-20,200,0],"aiden-horne":[-265,25,125,410,0,390,0,0,-20,200,0],"asa-hall":[-5,95,130,0,0,0,0,0,-20,200,0],"billy-tucker":[-35,0,115,0,0,0,0,0,-20,200,0],"caleb-pryce-hall":[0,0,100,0,0,0,0,0,-20,115,0],"corey-koerner":[10,0,110,0,0,0,0,0,-20,200,0],"dan-koita":[-25,-5,100,0,0,0,0,0,-20,200,0],"ed-palmer":[-500,80,125,465,0,440,0,0,-20,200,0],"finn-hodge":[-380,35,120,435,0,430,0,0,-20,200,0]};
const tivvyCardYellow="https://static.wixstatic.com/media/8aa829_81efb7b2c16545dd9be6c263ddacfeae~mv2.png";
const tivvyCardPurple="https://static.wixstatic.com/media/8aa829_577ea00227df4e88a88a3b109b717166~mv2.png";
function tivvyArtworkHeader(name, heading){
  const id=String(name||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const photo=tivvyCardPhotos[id];
  if(!photo) return '<div class="tivvyArtText"><p>YOUR TIVVY · PLAYER PROFILE</p><h3 id="profileName" tabindex="-1">'+heading+'</h3><span class="tivvyLeague">2026/27 · SOUTHERN LEAGUE DIVISION ONE SOUTH</span></div>';
  const values=tivvyCardPlacements[id]||[-25,0,100,0,0,0,0,0,-20,200,0];
  const [px,py,ps,nx,ny,x,y,bx,by,bs]=values;
  const sw=id==='louis-smith'?tivvyCardPurple:tivvyCardYellow;
  const attr=(s)=>String(s).replace(/"/g,'&quot;');
  return '<div class="tivvyArtStage">'+
    '<img class="tivvyArtSwipe" alt="" aria-hidden="true" src="'+sw+'" style="transform:translate('+bx+'px,'+by+'px) scale('+(bs/100)+')">'+
    '<div class="tivvyArtName" style="transform:translate('+nx+'px,'+ny+'px)"><p>YOUR TIVVY · PLAYER PROFILE</p><h3 id="profileName" tabindex="-1">'+heading+'</h3></div>'+
    '<img class="tivvyArtPhoto" alt="" aria-hidden="true" src="'+attr(photo)+'" style="transform:translate('+px+'px,'+py+'px) scale('+(ps/100)+')">'+
    '</div><div class="tivvyLeague">2026/27 · SOUTHERN LEAGUE DIVISION ONE SOUTH</div>';
}

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
          onMinute: p.onMinute || '', offMinute: p.offMinute || '', goalMinutes: p.goalMinutes || [], penaltyMinutes: [...penaltyMinutes],
          report: f.officialReportUrl || '', crest: f.opponentLogoUrl || ''});
      }
    }
  });
  return [...profiles.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/* Curated club history is independent of the live league totals. */
function playerCareerMarkup(entry, state = 'ready') {
  const safeURL = value => {
    try { const url = new URL(value); return url.protocol === 'https:' && ['www.tivvyarchive.co.uk','tivvyarchive.co.uk','www.tivertontownfc.uk','en.wikipedia.org'].includes(url.hostname) ? url.href : ''; }
    catch (_) { return ''; }
  };
  const archive = safeURL(entry?.archiveUrl) || 'https://www.tivvyarchive.co.uk/players.php';
  const clubs = Array.isArray(entry?.clubs) ? entry.clubs.filter(c => c && typeof c.club === 'string' && c.club.trim()) : [];
  const sources = Array.isArray(entry?.sources) ? entry.sources.filter(s => safeURL(s.url)) : [];
  return '<section class="profile-panel profile-previous-clubs" aria-label="Previous clubs"><h4>PREVIOUS CLUBS</h4>' +
    (clubs.length ? '<ul class="profile-clubs">' + clubs.map(c => '<li><strong>' + esc(c.club) + '</strong>' +
      (c.period ? '<span class="profile-club-period">' + esc(c.period) + '</span>' : '') +
      (c.note ? '<span class="profile-club-note">' + esc(c.note) + '</span>' : '') + '</li>').join('') + '</ul>' :
      '<p class="profile-note">' + (state === 'loading' ? 'Loading club history…' : state === 'error' ? 'Club history is temporarily unavailable.' : 'Previous club details have not yet been confirmed.') + '</p>') +
    '<div class="profile-career-footer"><p>' + (clubs.length ? 'Selected clubs · dates where confirmed. ' : '') +
    'With thanks to <a href="' + esc(archive) + '" target="_blank" rel="noopener noreferrer">Tivvy Archive ↗</a></p>' +
    (sources.length ? '<details class="profile-career-sources"><summary>Sources</summary><ul>' + sources.map(s => '<li><a href="' + esc(safeURL(s.url)) + '" target="_blank" rel="noopener noreferrer">' + esc(s.label || 'Club history source') + ' ↗</a></li>').join('') + '</ul></details>' : '') + '</div></section>';
}

(function () {
  let profiles = [], current = '', pending = new URLSearchParams(location.search).get('player') || '';
  const host = document.getElementById('playerProfile');
  if (!host) return;
  const node = id => document.getElementById(id);
  const embedded = window.parent !== window;
  let careerPlayers = [], careerState = 'loading';
  function updateCareer() {
    const target = node('profileCareer');
    if (!target || !current) return;
    target.innerHTML = playerCareerMarkup(careerPlayers.find(p => playerKey(p.name) === playerKey(current)), careerState);
    message({type:'tivvy-player-resize'});
  }
  fetch('player-career-history.json?v=20261027', {cache:'no-cache'})
    .then(response => { if (!response.ok) throw new Error('Club history unavailable'); return response.json(); })
    .then(data => { if (!Array.isArray(data.players)) throw new Error('Invalid club history'); careerPlayers = data.players; careerState = 'ready'; updateCareer(); })
    .catch(() => { careerState = 'error'; updateCareer(); });
  const message = data => { if (embedded) window.parent.postMessage(data, location.origin); };
  const find = name => profiles.find(p => playerKey(p.name) === playerKey(name));
  const stat = (value, label, red = false) => '<div class="profile-stat"><strong' + (red ? ' class="profile-goals"' : '') + '>' + esc(value) + '</strong><span>' + esc(label) + '</span></div>';
  const nameButton = name => '<button type="button" class="player-name-link" data-player-name="' + esc(name) + '">' + esc(name) + ' <span class="player-link-arrow" aria-hidden="true">↗︎</span></button>';
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
    const events = [];
    if (!m.used) events.push('<span class="player-unused">Unused substitute</span>');
    else {
      if (m.start) events.push('<span>Started</span>');
      else events.push('<span class="player-on">▲ on' + (m.onMinute ? ' ' + esc(m.onMinute) + '′' : '') + '</span>');
      if (m.offMinute) events.push('<span class="player-off">▼ off ' + esc(m.offMinute) + '′</span>');
      events.push('<span>≈' + m.mins + ' min</span>');
      if (m.captain) events.push('<span class="player-captain">(C)</span>');
    }
    let goals = '';
    if (m.goals) {
      goals = m.goalMinutes.length ? m.goalMinutes.map(time =>
        '<span class="profile-goal-event">' + ((m.penaltyMinutes || []).includes(String(time)) ? '<span class="player-penalty">⚽ PEN</span>' : '⚽') +
        ' <span class="goal-time">' + esc(time) + '′</span></span>').join(' ') :
        '<span class="profile-goal-event">⚽ <span class="goal-time">' + m.goals + (m.goals === 1 ? ' goal' : ' goals') + '</span></span>';
    }
    const score = parseScore(m.result);
    const img = crestUrl(m.opponent) || m.crest;
    return '<a class="profile-match' + (compact ? ' compact' : '') + '" href="' + esc(matchURL(m)) + '" data-profile-match="' + esc(JSON.stringify({date:m.date,opponent:m.opponent,venue:m.venue})) + '">' +
      '<span class="profile-result result-' + m.outcome.toLowerCase() + '">' + m.outcome + '</span>' +
      '<span class="profile-match-main"><span class="profile-opponent">' + (img && /^https:\/\//.test(img) ? '<img src="' + esc(img) + '" alt="" loading="lazy" onerror="this.remove()">' : '') + esc(m.opponent) + ' <small>' + (m.venue === 'H' ? 'HOME' : 'AWAY') + '</small></span>' +
      '<span class="profile-match-meta">' + esc(fmt(m.date)) + '</span></span>' +
      '<span class="profile-score">' + (m.venue === 'A' ? score.ga + '–<b>' + score.gf + '</b>' : '<b>' + score.gf + '</b>–' + score.ga) + '<span>DETAILS ↗︎</span></span>' +
      '<span class="profile-match-events"><span class="profile-appearance-events">' + events.join('<span class="profile-event-dot" aria-hidden="true"> · </span>') + '</span>' +
      (goals ? '<span class="profile-match-goals">' + goals + '</span>' : '') + '</span></a>';
  }

  function compare() {
    const p = find(current), other = find(node('profileCompareSelect').value), target = node('profileComparison');
    if (!p || !other) { target.innerHTML = '<p class="profile-note">Choose a teammate to compare their league season.</p>'; return; }
    const rows = [['Appearances','apps'],['Starts','starts'],['Sub appearances','subs'],['Estimated minutes','mins'],['Goals','goals'],['Captaincies','caps']];
    target.innerHTML = '<table class="profile-compare-table"><thead><tr><th scope="col">Statistic</th><th scope="col">' + esc(p.name) + '</th><th scope="col">' + esc(other.name) + '</th></tr></thead><tbody>' + rows.map(([label,key]) => '<tr><th scope="row">' + label + '</th><td' + (key === 'goals' ? ' class="profile-goals"' : '') + '>' + p[key] + '</td><td' + (key === 'goals' ? ' class="profile-goals"' : '') + '>' + other[key] + '</td></tr>').join('') + '</tbody></table>';
  }
  function playerHeading(name) {
    const [first, ...rest] = playerName(name).split(/\s+/);
    return '<span class="profile-given-name">' + esc(first) + '</span>' + (rest.length ? '<span class="profile-family-name">' + esc(rest.join(' ')) + '</span>' : '');
  }
  function show(name, focus = true) {
    if (!profiles.length) { pending = name; return; }
    const p = find(name) || {name:playerName(name),apps:0,starts:0,subs:0,mins:0,goals:0,caps:0,unused:0,homeGoals:0,awayGoals:0,penaltyGoals:0,timedGoals:0,goalBands:[0,0,0,0,0,0],matches:[]};
    current = p.name; pending = ''; const oldCompare = node('profileCompareSelect')?.value || '';
    const appearances = p.matches.filter(m => m.used), latest = appearances.slice(-5).reverse();
    const labels = ['1–15','16–30','31–45+','46–60','61–75','76–90+'], max = Math.max(1,...p.goalBands);
    host.innerHTML = '<div class="profile-toolbar"><button type="button" class="profile-back" id="profileBack">← ALL PLAYERS</button><label class="profile-switch-label">PLAYER<select id="profilePlayerSelect" aria-label="Choose player profile">' + (find(p.name)?profiles:[p,...profiles]).map(x=>'<option'+(x.name===p.name?' selected':'')+'>'+esc(x.name)+'</option>').join('') + '</select></label></div>' +
      '<div class="profile-hero tivvyArtworkProfile">' + tivvyArtworkHeader(p.name, playerHeading(p.name)) + '</div>' +
      '<div class="profile-stats">' + stat(p.apps,'Appearances') + stat(p.starts,'Starts') + stat(p.subs,'Sub on') + stat(p.mins,'Est. minutes') + stat(p.goals,'Goals',true) + stat(p.caps,'Captaincies') + '</div>' +
      '<p class="profile-note">Recorded league team sheets only. Minutes are estimates. Unused substitute: ' + p.unused + ' match' + (p.unused===1?'':'es') + '.</p>' +
      '<div id="profileCareer">' + playerCareerMarkup(careerPlayers.find(entry => playerKey(entry.name) === playerKey(p.name)), careerState) + '</div>' +
      '<section class="profile-panel"><h4>LAST FIVE APPEARANCES</h4><p class="profile-note">Latest first · W/D/L is the team result.</p><div>' + (latest.map(m=>matchCard(m,true)).join('') || '<p class="profile-note">No recorded league appearances yet.</p>') + '</div></section>' +
      '<section class="profile-panel profile-history"><h4>THE SEASON, MATCH BY MATCH</h4><p class="profile-note">Tap a match for its line-up, report and available photos.</p>' + (p.matches.slice().reverse().map(m=>matchCard(m,false)).join('') || '<p class="profile-note">No league team-sheet records available for this player.</p>') + '</section>' +
      '<section class="profile-panel"><h4>THE GOAL BREAKDOWN</h4><div class="profile-goal-split">' + stat(p.homeGoals,'At home',true) + stat(p.awayGoals,'Away',true) + '</div><p class="profile-note">' + p.penaltyGoals + ' penalty goal' + (p.penaltyGoals===1?'':'s') + ' explicitly recorded · ' + (p.goals-p.penaltyGoals) + ' other / unclassified goals.</p><div class="profile-goal-bands">' + labels.map((label,i)=>'<div class="profile-goal-band"><span>'+label+'′</span><span class="profile-bar"><i style="width:'+(100*p.goalBands[i]/max)+'%"></i></span><strong>'+p.goalBands[i]+'</strong></div>').join('') + '</div><p class="profile-note">' + (p.goals ? p.timedGoals + ' of ' + p.goals + ' goals have a recorded minute. Stoppage time stays with its half.' : 'No league goals recorded yet.') + '</p></section>' +
      '<section class="profile-panel profile-compare"><h4>HEAD TO HEAD</h4><div class="profile-compare-control"><label for="profileCompareSelect">Compare ' + esc(p.name) + ' with</label><select id="profileCompareSelect"><option value="">Choose a teammate…</option>' + profiles.filter(x=>x.name!==p.name).map(x=>'<option'+(x.name===oldCompare?' selected':'')+'>'+esc(x.name)+'</option>').join('') + '</select></div><div id="profileComparison"></div></section>';
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
