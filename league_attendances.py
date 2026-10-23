"""Read published crowds from the league's rendered, public match pages.

Only enrich completed league fixtures; leave every other match field intact.
The checked-in seed keeps verified figures available if the league is unavailable.
"""
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
CLUB_URL = 'https://www.southern-football-league.co.uk/clubs/tiverton-town'

def club(value):
    value = re.sub(r'[^a-z0-9]', '', value.lower())
    return {'hartpuryfc': 'hartpury', 'hartpuryuniversity': 'hartpury',
            'dorchester': 'dorchestertown', 'portlandutd': 'portlandunited',
            'weymouthfc': 'weymouth', 'slimbridgeafc': 'slimbridge',
            'swindonsm': 'swindonsupermarine', 'bidefordafc': 'bideford',
            'westbury': 'westburyunited'}.get(value, value)

def identity(f):
    return f['date'], club(f['opponent']), f['venue']

def apply_seed(data):
    seeds = json.loads((BASE / 'verified-attendances.json').read_text())['fixtures']
    seeds = {identity(f): f for f in seeds if f.get('competition') == 'SLD1S'}
    for fixture in data['fixtures']:
        seed = seeds.get(identity(fixture))
        if seed and fixture.get('result') and not fixture.get('upcoming'):
            fixture.update(attendance=seed['attendance'], attendanceSource=seed['attendanceSource'])
    return data

def refresh(data):
    apply_seed(data)
    # Scheduled builds do not commit data back to git. Retain the previous
    # published crowds when old games leave the league's recent-match feed.
    try:
        with urllib.request.urlopen('https://nickabull.github.io/Tiverton-Town-Get-Player-Info/data.json', timeout=20) as response:
            previous = {identity(f): f for f in json.load(response).get('fixtures', [])}
        for fixture in data['fixtures']:
            old = previous.get(identity(fixture), {})
            count = old.get('attendance')
            if not fixture.get('attendance') and fixture.get('result') and not fixture.get('upcoming') and isinstance(count, int) and count > 0:
                fixture.update(attendance=count, attendanceSource=old.get('attendanceSource', ''))
    except Exception as exc:
        print(f'Previous attendance cache unavailable: {type(exc).__name__}')
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            # Chrome is installed on the Windows GitHub Actions runner.
            browser = pw.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page()
            page.add_locator_handler(page.get_by_role('button', name='Accept all', exact=True), lambda locator: locator.click())
            page.goto(CLUB_URL, wait_until='domcontentloaded', timeout=45000)
            # This site publishes its fixture feed after hydration.
            page.get_by_role('tab', name='Matches', exact=True).click(timeout=30000)
            page.locator('.club-fixture-list__feed-row').first.wait_for(timeout=30000)
            rows = page.locator('.club-fixture-list__feed-row').evaluate_all('''es => es.map(e => ({
                date:e.querySelector('.club-fixture-list__rail-date')?.textContent,
                competition:e.querySelector('.club-fixture-list__rail-comp')?.textContent,
                opponent:e.querySelector('.club-fixture-list__opponent-name')?.textContent,
                venue:e.querySelector('.club-fixture-list__venue')?.textContent,
                source:e.querySelector('a')?.href
            }))''')
            checked = 0
            for row in rows:
                if row.get('competition', '').strip() != 'Division One South':
                    continue
                matches = [f for f in data['fixtures'] if f.get('result') and not f.get('upcoming')
                           and club(f['opponent']) == club(row.get('opponent', ''))
                           and f['venue'] == row.get('venue', '').strip()
                           and (datetime.fromisoformat(f['date']).strftime('%a ') + str(datetime.fromisoformat(f['date']).day) + datetime.fromisoformat(f['date']).strftime(' %b')) == row.get('date', '').strip()]
                if len(matches) != 1 or not re.fullmatch(r'https://www\.southern-football-league\.co\.uk/match/[a-f0-9]+', row.get('source', '')):
                    continue
                fixture = matches[0]
                try:
                    page.goto(row['source'], wait_until='domcontentloaded', timeout=30000)
                    attendance = page.locator('[aria-label^="Attendance:"]').first
                    attendance.wait_for(state='attached', timeout=15000)
                    label = attendance.get_attribute('aria-label') or ''
                    text = page.get_by_role('main').inner_text()
                    day = datetime.fromisoformat(fixture['date'])
                    expected_date = f'{day.day} {day.strftime("%b %Y")}'
                    if 'DIVISION ONE SOUTH' not in text.upper() or expected_date not in text or not re.search(r'\bFT\b', text):
                        continue
                    crowd = re.fullmatch(r'Attendance:\s*([\d,]+)', label)
                    if crowd and int(crowd[1].replace(',', '')) > 0:
                        fixture.update(attendance=int(crowd[1].replace(',', '')), attendanceSource=row['source'])
                        checked += 1
                except Exception as exc:
                    print(f'Attendance unavailable for {fixture["date"]}: {type(exc).__name__}')
            browser.close()
            print(f'Southern League attendances refreshed: {checked}')
    except Exception as exc:
        print(f'Southern League attendance refresh unavailable; retaining verified figures: {type(exc).__name__}: {exc}')
    return data

if __name__ == '__main__':
    data = refresh(json.loads((BASE / 'data.json').read_text(encoding='utf-8-sig')))
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    (BASE / 'data.json').write_text(raw, encoding='utf-8')
    (BASE / 'data.js').write_text('window.TIVVY_DATA = ' + raw + ';\n', encoding='utf-8')

