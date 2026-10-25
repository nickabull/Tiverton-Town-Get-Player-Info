"""Discover published club reports without altering scores or team sheets."""
import calendar
import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
FEED = 'https://www.tivertontownfc.uk/blog-feed.xml'


def clean(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def discover(xml, fixtures):
    found = []
    for item in ET.fromstring(xml).findall('.//item'):
        description = html.unescape(item.findtext('description') or '')
        description = re.sub(r'<[^>]+>', ' ', description)
        if not re.search(r'(?<!preview by )\breport by Darren Holmes\b', description, re.I):
            continue
        prefix = description.split('|')[0].strip()
        score = re.fullmatch(r'(.+?)\s+(\d+)\s*[-–]?\s+(.+?)\s+(\d+)', prefix)
        link = (item.findtext('link') or '').strip()
        url = urlparse(link)
        if not score or url.scheme != 'https' or url.netloc != 'www.tivertontownfc.uk' or not url.path.startswith('/post/'):
            continue
        try:
            published = parsedate_to_datetime(item.findtext('pubDate')).date()
        except (ValueError, TypeError):
            continue
        home, hg, away, ag = score.groups()
        candidates = []
        for fixture in fixtures:
            day = date.fromisoformat(fixture['date'])
            # The report must name the fixture's day/month, as well as its score.
            month = calendar.month_name[day.month]
            named_day = (rf'\b{month}\s+{day.day}(?:st|nd|rd|th)?\b|'
                         rf'\b{day.day}(?:st|nd|rd|th)?\s+{month}\b')
            if not 0 <= (published - day).days <= 7 or not re.search(named_day, description, re.I):
                continue
            result = re.search(r'(\d+)\s*-\s*(\d+)', fixture.get('result', ''))
            if not result:
                continue
            tg, og = result.groups()
            opponent = clean(fixture['opposition'])
            ours = {'tiverton', 'tiverton town', 'tiverton town fc'}
            if fixture['homeAway'] == 'H':
                match = clean(home) in ours and clean(away) == opponent and (hg, ag) == (tg, og)
            else:
                match = clean(away) in ours and clean(home) == opponent and (ag, hg) == (tg, og)
            if match:
                candidates.append(fixture)
        if len(candidates) == 1:
            f = candidates[0]
            found.append(dict(date=f['date'], opponent=f['opposition'], venue=f['homeAway'],
                              officialReportUrl=link))
    return found


def main():
    path = BASE / 'match-report-links.json'
    saved = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'reports': []}
    fixtures = json.loads((BASE / 'match-centre-fixtures-2026-27.json').read_text(encoding='utf-8'))['fixtures']
    try:
        request = urllib.request.Request(FEED, headers={'User-Agent': 'TivvyMatchCentre/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            reports = discover(response.read(), fixtures)
        known = {(r['date'], r['opponent'], r['venue']): r for r in saved['reports']}
        for report in reports:
            known[(report['date'], report['opponent'], report['venue'])] = report
        saved['reports'] = sorted(known.values(), key=lambda r: (r['date'], r['opponent'], r['venue']))
        path.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"Matched {len(reports)} published Darren reports; {len(known)} retained links.")
    except Exception as error:
        print(f'Report feed unavailable ({type(error).__name__}); retaining saved report links.')
    # Apply saved links even when the network is unavailable. Existing line-ups stay intact.
    for name in ['data.json', 'cup-match-details-2026-27.json', 'historical-match-details-2026-27.json']:
        target = BASE / name
        data = json.loads(target.read_text(encoding='utf-8-sig'))
        for fixture in data['fixtures']:
            for report in saved['reports']:
                if (fixture.get('date'), clean(fixture.get('opponent', '')), fixture.get('venue')) == (report['date'], clean(report['opponent']), report['venue']):
                    fixture['officialReportUrl'] = report['officialReportUrl']
        raw = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        target.write_text(raw + '\n', encoding='utf-8')
        if name == 'data.json':
            (BASE / 'data.js').write_text('window.TIVVY_DATA = ' + raw + ';\n', encoding='utf-8')


if __name__ == '__main__':
    main()
