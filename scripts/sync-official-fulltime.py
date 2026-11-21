#!/usr/bin/env python3
"""Import verified final Southern League results into the Wix-backed match centre.
Only updates a scheduled league fixture when official status is FULL TIME.
Leaves existing detailed records, manual editorial fields, and other competitions alone.
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "match-centre-fixtures-2026-27.json"
DETAILS = ROOT / "data.json"
API = "https://tivvy-live-collector.nickabull.workers.dev/live"
FWP_RESULTS = "https://nickabull.github.io/Tiverton-Town-Get-Results/data.json"
def fixture_dates(fixtures):
    """Discover recent league fixtures every run, including midweek and today.

    Keep completed recent fixtures in scope so corrected official finals can
    trigger explicit conflict review, rather than silently being ignored.
    """
    today = datetime.now(timezone.utc).date()
    earliest = today - timedelta(days=21)
    dates = set()
    for fixture in fixtures.get("fixtures", []):
        if fixture.get("competition") != "SLD1S":
            continue
        try:
            match_date = date.fromisoformat(fixture["date"])
        except (ValueError, KeyError, TypeError):
            continue
        if earliest <= match_date <= today:
            dates.add(match_date.isoformat())
    return sorted(dates)

def fetch(date):
    url = API + "?date=" + date
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "TivvyResultSynchroniser/1.0"})
    with urlopen(req, timeout=30) as response:
        record = json.load(response)
    matchday = record.get("matchday") or {}
    featured = matchday.get("featured") or {}
    if (matchday.get("status") != "ok" or matchday.get("date") != date or
        featured.get("status", "").lower() not in ("fulltime", "full time", "full_time")):
        return None
    score = featured.get("score") or {}
    if not all(isinstance(score.get(x), int) and score[x] >= 0 for x in ("home", "away")):
        return None
    if featured.get("home", "").lower() == "tiverton town":
        venue, opposition = "H", featured.get("away")
        for_, against = score["home"], score["away"]
    elif featured.get("away", "").lower() == "tiverton town":
        venue, opposition = "A", featured.get("home")
        for_, against = score["away"], score["home"]
    else:
        return None
    if not opposition:
        return None
    return {"date": date, "venue": venue, "opposition": opposition,
            "goalsFor": for_, "goalsAgainst": against, "score": score,
            "events": featured.get("events") or [], "matchId": featured.get("id")}

def fetch_fwp_completed():
    """Read the existing FWP-backed Results Centre's completed-score feed.

    This is a fallback for *scores only*, never lineup, player event or
    league-position verification. Its fixture list contains finished scores.
    """
    req = Request(FWP_RESULTS + "?postmatch=1", headers={
        "Accept": "application/json", "User-Agent": "TivvyResultSynchroniser/1.1"})
    with urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if "footballwebpages.co.uk" not in str(payload.get("source", "")):
        raise ValueError("Unexpected Results Centre provenance")
    if not isinstance(payload.get("results"), list) or len(payload["results"]) < 20:
        raise ValueError("Incomplete Results Centre results feed")
    return payload["results"]


def fallback_result(date, fixture, completed):
    """Return one unambiguous, dated FWP final for this scheduled match."""
    venue = fixture.get("homeAway")
    if venue not in ("H", "A"):
        return None
    expected_home = "Tiverton Town" if venue == "H" else fixture.get("opposition")
    expected_away = fixture.get("opposition") if venue == "H" else "Tiverton Town"
    possible = [m for m in completed if m.get("date") == date and
                normal(m.get("home")) == normal(expected_home) and
                normal(m.get("away")) == normal(expected_away)]
    if len(possible) != 1:
        return None
    import re
    score = re.fullmatch(r"(\\d+)-(\\d+)", str(possible[0].get("score", "")))
    if not score:
        return None
    home, away = map(int, score.groups())
    if home > 30 or away > 30:
        return None
    return {"date": date, "venue": venue, "opposition": fixture["opposition"],
            "goalsFor": home if venue == "H" else away,
            "goalsAgainst": away if venue == "H" else home,
            "score": {"home": home, "away": away}, "events": [], "matchId": None,
            "sourceUrl": FWP_RESULTS, "sourceName": "Football Web Pages completed results",
            "eventDetailsVerified": False}


def normal(name):
    return "".join(ch for ch in str(name).lower() if ch.isalnum())

def scorers(record):
    found = []
    # Goals in score progression for Tiverton, never guess from display name alone.
    prev = {"home": 0, "away": 0}
    team_side = "home" if record["venue"] == "H" else "away"
    for e in sorted(record["events"], key=lambda x: (int(x.get("minute") or 0), x.get("createdAt", ""))):
        score = e.get("score") or {}
        if str(e.get("eventType", "")).startswith("GOAL") and score.get(team_side, 0) > prev[team_side]:
            person = (e.get("person") or {}).get("name")
            if person:
                minute = e.get("minute")
                pen = " (pen)" if "PENALTY" in e.get("eventType", "") else ""
                found.append(f"{person} {minute}'{pen}")
        if isinstance(score.get("home"), int) and isinstance(score.get("away"), int):
            prev = score
    return ", ".join(found)

def save_if_changed(path, old, new):
    if old != new:
        path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n")
        print("UPDATED", path.name)
    else:
        print("UNCHANGED", path.name)

def main():
    fixtures = json.loads(FIXTURES.read_text())
    details = json.loads(DETAILS.read_text())
    original_f = json.dumps(fixtures, sort_keys=True)
    original_d = json.dumps(details, sort_keys=True)
    try:
        completed = fetch_fwp_completed()
    except Exception as exc:
        completed = []
        print(f"WARN Results Centre fallback unavailable: {type(exc).__name__}: {exc}", file=sys.stderr)
    for date in fixture_dates(fixtures):
        try:
            match = fetch(date)
        except Exception as exc:
            print(f"WARN {date}: collector unavailable ({type(exc).__name__}); keeping verified data", file=sys.stderr)
            continue
        if not match:
            candidates = [f for f in fixtures["fixtures"] if f.get("date") == date and
                          f.get("competition") == "SLD1S" and not f.get("result")]
            fallback = [fallback_result(date, f, completed) for f in candidates]
            fallback = [m for m in fallback if m]
            if len(fallback) == 1:
                match = fallback[0]
                print("FWP COMPLETED RESULT FALLBACK", date, match["opposition"])
        if not match:
            print("SKIP", date, "no verified completed result available")
            continue
        candidate = next((f for f in fixtures["fixtures"] if f["date"] == date and
            f.get("competition") == "SLD1S" and f.get("homeAway") == match["venue"] and
            normal(f.get("opposition")) == normal(match["opposition"])), None)
        if not candidate:
            print("WARN", date, "no uniquely matching scheduled league fixture; no data changed", file=sys.stderr)
            continue
        result = "W" if match["goalsFor"] > match["goalsAgainst"] else "L" if match["goalsFor"] < match["goalsAgainst"] else "D"
        score_fixture = f'{match["score"]["home"]}-{match["score"]["away"]}'
        new_result = f"{result} {score_fixture}"
        if candidate.get("result") and candidate["result"] != new_result:
            print("WARN", date, "existing final result conflicts; needs review", file=sys.stderr)
            continue
        candidate["result"] = new_result
        if not candidate.get("scorers"):
            candidate["scorers"] = scorers(match)
        # A lineup cannot be inferred from goals/substitutions; retain an existing record if present.
        detail = next((x for x in details["fixtures"] if x["date"] == date and
            x.get("venue") == match["venue"] and normal(x.get("opponent")) == normal(match["opposition"])), None)
        result_for_against = f'{match["goalsFor"]}-{match["goalsAgainst"]}'
        if detail is None:
            detail = {"date": date, "venue": match["venue"], "opponent": match["opposition"],
                "opponentLogoUrl": "", "result": result_for_against, "goalscorers": scorers(match),
                "starters": [], "subs": [], "starterDetails": [], "subDetails": [], "players": [],
                "squadUrl": "", "fwpUrl": "", "officialReportUrl": "", "upcoming": False,
                "detailsLevel": "result-and-incidents-only",
                "eventSource": match.get("sourceUrl") or ("https://www.southern-football-league.co.uk/match/" + str(match["matchId"])),
                "notes": "Automatically imported verified final result. Starting XI/unused substitutes require a separate verified lineup source."}
            details["fixtures"].append(detail)
        elif detail.get("result") != result_for_against:
            print("WARN", date, "detailed match record conflicts; retaining existing data", file=sys.stderr)
            continue
        else:
            detail["upcoming"] = False
        print("VERIFIED SOURCE", match.get("sourceName", "Official Southern League"), date, match["opposition"], new_result)
    if json.dumps(fixtures, sort_keys=True) != original_f:
        fixtures["updated"] = datetime.now(timezone.utc).isoformat() + " - verified full-time import"
    if json.dumps(details, sort_keys=True) != original_d:
        details["updated"] = datetime.now(timezone.utc).isoformat()
        details["fixtures"].sort(key=lambda x: x["date"])
    save_if_changed(FIXTURES, json.loads(FIXTURES.read_text()), fixtures)
    save_if_changed(DETAILS, json.loads(DETAILS.read_text()), details)

if __name__ == "__main__":
    main()
