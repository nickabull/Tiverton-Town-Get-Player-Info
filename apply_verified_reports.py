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
        data['fixtures'] = [f for f in data['fixtures'] if not (f['date'] == fixture['date'] and f['opponent'] == fixture['opponent'])]
        data['fixtures'].append(fixture)
    data['fixtures'].sort(key=lambda f: f['date'])
    data['updated'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    return data

if __name__ == '__main__':
    data = apply(json.loads((BASE / 'data.json').read_text(encoding='utf-8-sig')))
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    (BASE / 'data.json').write_text(raw)
    (BASE / 'data.js').write_text('window.TIVVY_DATA = ' + raw + ';\n')
    print(f"Verified club reports applied: {len(data['fixtures'])} league fixtures")
