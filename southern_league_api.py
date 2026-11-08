#!/usr/bin/env python3
"""Southern League public match API -> cautious Tivvy match-event staging.

The league's /matches?withEvents=1 response is useful, but cannot be treated
as an authoritative replacement for corrected club teamsheets. Default mode
writes a reviewable audit; --apply additionally fills ONLY unverified fixtures
when the API contains a complete, unambiguous match record.
"""
import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
ENDPOINT = "https://api.southern-football-league.co.uk/matches"


def canonical(name):
    value = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    return re.sub(r"(?:afc|fc)$", "", value)


def minute(value):
    return "" if value is None else str(value)


def events(match, field):
    value = match.get(field)
    return value if isinstance(value, list) else []


def person(name, number=None, sub=False):
    return dict(name=str(name), number=number, captain=False, position=None,
                onMinute="", offMinute="", goalCount=0, goalMinutes=[],
                sub=sub, used=not sub, cards=[])


def team_name(match, side):
    item = match.get(side + "Team") or {}
    if isinstance(item, dict):
        return item.get("fullName") or item.get("shortName") or match.get(side + "TeamName") or ""
    return match.get(side + "TeamName") or ""


def match_date(match):
    for key in ("startDate", "matchDate", "date", "kickOff", "kickoff", "scheduledAt"):
        value = match.get(key)
        if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}", value):
            return value[:10]
    return ""


def full_time(match):
    return str(match.get("status") or match.get("externalMatchStatus") or "").lower() in (
        "fulltime", "full_time", "finished", "final"
    )


def get_score(match):
    score = match.get("score") or {}
    current = score.get("current", {}) if isinstance(score, dict) else {}
    try:
        return int(current["home"]), int(current["away"])
    except (ValueError, TypeError, KeyError):
        return None


def extract_match(match):
    home = team_name(match, "home")
    away = team_name(match, "away")
    if canonical(home) != "tivertontown" and canonical(away) != "tivertontown":
        return None
    venue = "H" if canonical(home) == "tivertontown" else "A"
    opponent = away if venue == "H" else home
    score = get_score(match)
    source = "https://www.southern-football-league.co.uk/match/" + str(match.get("_id") or match.get("id") or "")
    side = "home" if venue == "H" else "away"
    data = {
        "date": match_date(match), "venue": venue, "opponent": opponent,
        "source": source, "apiId": str(match.get("_id") or match.get("id") or ""),
        "status": match.get("status"), "score": score,
        "attendance": match.get("attendance"),
        "goals": events(match, side + "Goals"),
        "cards": events(match, side + "Cards"),
        "subs": events(match, side + "Subs"),
        "lineup": next((events(match, side + key) for key in
                        ("Lineup", "StartingLineup", "StartingXI", "Starters", "Lineups")
                        if events(match, side + key)), []),
        "bench": next((events(match, side + key) for key in
                       ("Bench", "Substitutes", "BenchPlayers")
                       if events(match, side + key)), []),
    }
    return data


def fetch(day):
    params = {
        "withEvents": 1, "period": "Custom",
        "startDate": day + "T00:00:00.000Z",
        "endDate": day + "T23:59:59.999Z",
        "limit": 1000, "status": "any",
    }
    request = Request(ENDPOINT + "?" + urlencode(params), headers={
        "Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; TivertonTownMatchCentre/1.0)",
        "Origin": "https://www.southern-football-league.co.uk",
        "Referer": "https://www.southern-football-league.co.uk/live",
        "X-TENANT-ID": "sfl",  # Public tenant identifier in the league site configuration
    })
    with urlopen(request, timeout=25) as response:
        body = json.loads(response.read(8_000_000).decode("utf-8"))
    if not isinstance(body, dict) or not isinstance(body.get("items"), list):
        raise ValueError("API returned unexpected response shape (expected items array)")
    return body["items"]


def normalise_event(value):
    if not isinstance(value, dict):
        return {}
    return {k: value.get(k) for k in (
        "minute", "personName", "personOnName", "personOffName", "cardType",
        "goalType", "playerName", "scorerName", "phase"
    ) if k in value}


def compact(match):
    return {k: ([normalise_event(v) for v in value] if k in ("goals","cards","subs","lineup","bench") else value)
            for k, value in match.items()}


def fixture_match(f, record):
    return f.get("date") == record.get("date") and f.get("venue") == record.get("venue") and (
        canonical(f.get("opponent")) == canonical(record.get("opponent")))


def make_player_details(record):
    """Only accept explicit structured XI/bench; never infer a full teamsheet from substitutions."""
    starters = record["lineup"]
    bench = record["bench"]
    def extract(row, sub):
        if not isinstance(row, dict):
            return None
        name = row.get("personName") or row.get("playerName") or row.get("name")
        if not name:
            return None
        p = person(name, row.get("number") or row.get("shirtNumber"), sub)
        p["position"] = "GK" if row.get("isGoalkeeper") else None
        p["captain"] = bool(row.get("isCaptain"))
        return p
    first = [extract(p, False) for p in starters]
    second = [extract(p, True) for p in bench]
    if len(first) != 11 or any(p is None for p in first) or any(p is None for p in second):
        return None
    everyone = first + second
    if len({canonical(p["name"]) for p in everyone}) != len(everyone):
        return None
    byname = {canonical(p["name"]): p for p in everyone}
    for e in record["subs"]:
        off, on = byname.get(canonical(e.get("personOffName"))), byname.get(canonical(e.get("personOnName")))
        if off and on and off in first and on in second:
            off["offMinute"] = minute(e.get("minute"))
            on["onMinute"] = minute(e.get("minute"))
            on["used"] = True
    for e in record["cards"]:
        p = byname.get(canonical(e.get("personName")))
        if p:
            p["cards"].append({"type": str(e.get("cardType") or ""), "minute": minute(e.get("minute"))})
    for e in record["goals"]:
        p = byname.get(canonical(e.get("personName") or e.get("scorerName") or e.get("playerName")))
        if p:
            p["goalCount"] += 1
            p["goalMinutes"].append(minute(e.get("minute")))
    return first, second


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Matchday YYYY-MM-DD (default today UTC)")
    parser.add_argument("--sample", help="Offline JSON response fixture for testing")
    parser.add_argument("--apply", action="store_true", help="Fill complete UNVERIFIED matches only")
    parser.add_argument("--output", default="southern-league-api-audit.json")
    args = parser.parse_args(argv)
    day = args.date or datetime.now(timezone.utc).date().isoformat()
    date.fromisoformat(day)
    if args.sample:
        raw = json.loads(Path(args.sample).read_text(encoding="utf-8"))
        items = raw["items"] if isinstance(raw, dict) else raw
    else:
        items = fetch(day)
    selected = [v for item in items if isinstance(item, dict) if (v := extract_match(item))]
    selected = [v for v in selected if v["date"] in ("", day)]
    output = {"date": day, "checkedAt": datetime.now(timezone.utc).isoformat(),
              "api": ENDPOINT, "totalMatches": len(items), "tivertonMatches": [compact(v) for v in selected],
              "applied": [], "warnings": []}
    data_path = BASE / "data.json"
    fixture_path = BASE / "match-centre-fixtures-2026-27.json"
    verified_path = BASE / "verified-match-reports.json"
    if args.apply:
        data = json.loads(data_path.read_text(encoding="utf-8-sig"))
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
        verified = json.loads(verified_path.read_text(encoding="utf-8-sig"))
        for match in selected:
            candidates = [f for f in fixtures["fixtures"] if (
                f["date"] == match["date"] and f["homeAway"] == match["venue"]
                and canonical(f["opposition"]) == canonical(match["opponent"]))]
            protected = any(fixture_match(f, match) for f in verified["fixtures"])
            details = make_player_details(match)
            if protected:
                output["warnings"].append("Protected verified match left untouched: " + str(match["date"]))
                continue
            if len(candidates) != 1 or not full_time(match) or not match["score"] or details is None:
                output["warnings"].append("Insufficient API teamsheet/status or ambiguous fixture: " + str(match["date"]))
                continue
            home, away = match["score"]
            gf, ga = (home, away) if match["venue"] == "H" else (away, home)
            first, second = details
            if sum(p["goalCount"] for p in first+second) != gf:
                output["warnings"].append("Goal-event total mismatch: " + str(match["date"]))
                continue
            fixture = candidates[0]
            result = "W" if gf > ga else "D" if gf == ga else "L"
            fixture["result"] = f"{result} {gf}-{ga}"
            found = next((f for f in data["fixtures"] if fixture_match(f, match)), None)
            if found and found.get("starterDetails"):
                output["warnings"].append("Existing detailed record left untouched: " + str(match["date"]))
                continue
            record = dict(date=match["date"], venue=match["venue"], opponent=match["opponent"],
                          opponentLogoUrl="", result=f"{gf}-{ga}", goalscorers="",
                          starters=[p["name"] for p in first], subs=[p["name"] for p in second],
                          starterDetails=first, subDetails=second,
                          players=[p["name"] for p in first+second], upcoming=False,
                          squadUrl="", fwpUrl="", officialReportUrl="", eventSource=match["source"],
                          lineupSource=match["source"])
            data["fixtures"] = [f for f in data["fixtures"] if not fixture_match(f, match)] + [record]
            output["applied"].append(match["date"])
        if output["applied"]:
            data["fixtures"].sort(key=lambda x: x["date"])
            data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (BASE / "data.js").write_text("window.TIVVY_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
            fixture_path.write_text(json.dumps(fixtures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Southern League: {len(items)} fixtures; {len(selected)} Tiverton match(es); {len(output['applied'])} safely applied.")
    for warning in output["warnings"]:
        print("REVIEW:", warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())
