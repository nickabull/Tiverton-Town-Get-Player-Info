"""Keep published club team sheets available while the Archive catches up."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent

def apply(data):
    verified = json.loads((BASE / 'verified-match-reports.json').read_text())
    for date, url in verified['reportUrls'].items():
        for fixture in data['fixtures']:
            if fixture['date'] == date and fixture.get('result'):
                fixture['officialReportUrl'] = url
    for fixture in verified['fixtures']:
        assert len(fixture['starters']) == 11
        assert len(set(fixture['players'])) == len(fixture['players'])
        assert sum(p['goalCount'] for p in fixture['starterDetails'] + fixture['subDetails']) == int(fixture['result'].split('-')[0])
        # Match by date and venue as well as normalised club name. The scraper
        # sometimes includes an FC/AFC suffix which otherwise leaves a stale
        # duplicate ahead of the verified match in the Match Centre.
        def club_key(name):
            import re
            return re.sub(r'(?:afc|fc)
        data['fixtures'].append(fixture)
    data['fixtures'].sort(key=lambda f: f['date'])
    data['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    return data

if __name__ == '__main__':
    data = apply(json.loads((BASE / 'data.json').read_text(encoding='utf-8-sig')))
    from league_attendances import apply_seed
    data = apply_seed(data)
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    (BASE / 'data.json').write_text(raw, encoding='utf-8')
    (BASE / 'data.js').write_text('window.TIVVY_DATA = ' + raw + ';\n', encoding='utf-8')
    print(f"Verified club reports applied: {len(data['fixtures'])} league fixtures")

, '', re.sub(r'[^a-z0-9]', '', str(name).lower()))

        data['fixtures'] = [
            f for f in data['fixtures']
            if not (
                f['date'] == fixture['date']
                and f.get('venue') == fixture.get('venue')
                and club_key(f['opponent']) == club_key(fixture['opponent'])
            )
        ]
        data['fixtures'].append(fixture)
    data['fixtures'].sort(key=lambda f: f['date'])
    data['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    return data

if __name__ == '__main__':
    data = apply(json.loads((BASE / 'data.json').read_text(encoding='utf-8-sig')))
    from league_attendances import apply_seed
    data = apply_seed(data)
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    (BASE / 'data.json').write_text(raw, encoding='utf-8')
    (BASE / 'data.js').write_text('window.TIVVY_DATA = ' + raw + ';\n', encoding='utf-8')
    print(f"Verified club reports applied: {len(data['fixtures'])} league fixtures")

