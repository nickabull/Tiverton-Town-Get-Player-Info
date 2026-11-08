#!/usr/bin/env python3
"""Read-only Southern League endpoint diagnostic; no production files are altered.
Logs HTTP status, bounded non-sensitive response hints, and response envelope shape.
No credentials, tokens or cookies are used.
"""
import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE = "https://api.southern-football-league.co.uk/matches"
DAY = "2026-11-07"
QUERIES = [
    ("original", dict(withEvents="1", period="Custom", startDate=DAY+"T00:00:00.000Z", endDate=DAY+"T23:59:59.999Z", limit="1000", status="any")),
    ("no-status", dict(withEvents="1", period="Custom", startDate=DAY+"T00:00:00.000Z", endDate=DAY+"T23:59:59.999Z", limit="100")),
    ("basic-date", dict(startDate=DAY, endDate=DAY)),
    ("minimal", dict(limit="10")),
]
def redact(text):
    """Never print arbitrarily long API output or a possible encoded credential."""
    return "".join(c if c.isprintable() else " " for c in text)[:300]

results = []
for label, params in QUERIES:
    url = BASE+"?"+urlencode(params)
    request = Request(url, headers={"Accept":"application/json","User-Agent":"Mozilla/5.0 (compatible; TivertonTownMatchCentre/1.0)","Origin":"https://www.southern-football-league.co.uk","Referer":"https://www.southern-football-league.co.uk/live"})
    row = {"name":label,"status":None,"content_type":None,"response_shape":None,"tiverton_count":0,"body_hint":None}
    try:
        with urlopen(request, timeout=18) as response:
            row["status"] = response.status
            row["content_type"] = response.headers.get("Content-Type")
            body = response.read(700000)
        try:
            parsed = json.loads(body)
            row["response_shape"] = sorted(parsed.keys())[:20] if isinstance(parsed,dict) else type(parsed).__name__
            items = parsed.get("items", []) if isinstance(parsed,dict) else parsed if isinstance(parsed,list) else []
            row["tiverton_count"] = sum("tiverton" in json.dumps([x.get("homeTeam"),x.get("awayTeam")]).lower() for x in items if isinstance(x,dict))
            row["item_count"] = len(items)
            if row["tiverton_count"]:
                row["tiverton_sample_keys"] = sorted(next(x for x in items if isinstance(x,dict) and "tiverton" in json.dumps([x.get("homeTeam"),x.get("awayTeam")]).lower()).keys())
        except (ValueError,TypeError):
            row["body_hint"] = redact(body.decode("utf-8","replace"))
    except HTTPError as exc:
        row["status"] = exc.code
        row["content_type"] = exc.headers.get("Content-Type")
        row["body_hint"] = redact(exc.read(1200).decode("utf-8","replace"))
    except (URLError, TimeoutError, OSError) as exc:
        row["body_hint"] = redact(str(exc))
    results.append(row)
    print(json.dumps(row,ensure_ascii=False),flush=True)
with open("southern-league-endpoint-diagnostic.json","w",encoding="utf-8") as fp:
    json.dump({"checked_at":datetime.now(timezone.utc).isoformat(),"date":DAY,"tests":results},fp,indent=2)
    fp.write("\n")
sys.exit(0)
