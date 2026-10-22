#!/usr/bin/env python3
"""Conservative GitHub -> Wix LIVE fixture sync. Default is dry-run.
Requires WIX_API_KEY in env; never commit the key.
Matches by date, opponent, venue AND competition.
Only updates verified results/scorers. Never creates/deletes fixtures.
"""
import argparse
import datetime as dt
import json
import os
import re
import urllib.request

SITE_ID = "89bf836a-7450-45b2-9537-952edd3126c9"
COLLECTION = "Import1"
BASE = "https://www.wixapis.com"
REPO = "https://raw.githubusercontent.com/nickabull/Tiverton-Town-Get-Player-Info/main/"
def request(url, payload=None, method=None):
    headers = {"Content-Type":"application/json", "Authorization":os.environ["WIX_API_KEY"], "wix-site-id":SITE_ID}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ("POST" if data else "GET"))
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)
def public(name):
    with urllib.request.urlopen(REPO + name, timeout=30) as resp:
        return json.load(resp)
def key(s):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\\b(afc|fc)\\b", "",str(s or "").lower()))
def comp(s):
    s=key(s)
    if "stluke" in s:return "stlukescup"
    if "sld1s" in s or "southernleague" in s or "divisiononesouth" in s:return "league"
    if "facup" in s:return "facup"
    if "fatrophy" in s:return "fatrophy"
    return s
def venue(s):
    s=str(s or "").upper()
    return "H" if s in ("H","HOME") else "A" if s in ("A","AWAY") else "?"
def date(s):
    if isinstance(s,dict): s=s.get("$date","")
    return str(s or "")[:10]
def identity(d,is_wix=False):
    return (date(d.get("date")),key(d.get("opposition" if is_wix else "opponent")),
            venue(d.get("homeAway" if is_wix else "venue")),comp(d.get("competition")))
def wix_items():
    items=[]; cursor=None
    for _ in range(20):
        q={"paging":{"limit":100}}
        if cursor:q["paging"]["cursor"]=cursor
        data=request(BASE+"/wix-data/v2/items/query",{"dataCollectionId":COLLECTION,"query":q})
        items.extend(data.get("dataItems",[]))
        page=data.get("pagingMetadata",{})
        cursor=page.get("cursors",{}).get("next")
        if not page.get("hasNext") or not cursor:break
    return items
def source_fixtures():
    league=public("data.json").get("fixtures",[])
    cups=public("cup-match-details-2026-27.json").get("fixtures",[])
    records=[]
    for m in league:
        if m.get("result") and not m.get("upcoming"):
            records.append(dict(m, competition="SLD1S", _origin="league"))
    for m in cups:
        if m.get("result") and not m.get("upcoming"):
            records.append(dict(m, _origin="cup"))
    return records
def fields(m):
    result=str(m.get("result") or "").strip()
    mo=re.fullmatch(r"(\\d+)\\s*[-–]\\s*(\\d+)",result)
    if not mo:return {}
    goals_for,goals_against=map(int,mo.groups())
    prefix="W" if goals_for>goals_against else "D" if goals_for==goals_against else "L"
    # Wix results are displayed Tivvy-first, including away matches.
    out={"result":f"{prefix} {goals_for}-{goals_against}"}
    # Cup scorer field is verified. League goal strings must be generated
    # only when an existing curated string is available.
    if m.get("_origin")=="cup" and m.get("goalscorers"):
        out["scorers"]=m["goalscorers"]
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true",help="Write only reviewed, verified differences")
    a=p.parse_args()
    if not os.getenv("WIX_API_KEY"):
        raise SystemExit("Missing WIX_API_KEY secret. No changes made.")
    records=source_fixtures()
    wix=wix_items()
    by_key={}
    for item in wix:by_key.setdefault(identity(item.get("data",{}),True),[]).append(item)
    planned=[]
    for m in records:
        ident=identity(m)
        matches=by_key.get(ident,[])
        if len(matches)!=1: 
            print("SKIP missing/ambiguous",ident,"matches",len(matches))
            continue
        item=matches[0]; old=item["data"]; wanted=fields(m)
        changes={field:new for field,new in wanted.items() if old.get(field)!=new}
        # An already populated result that DISAGREES with feed needs manual review.
        if "result" in changes and str(old.get("result") or "").strip():
            print("REVIEW conflicting result",ident,"Wix:",old.get("result"),"feed:",wanted["result"])
            continue
        if changes:planned.append((item["id"],ident,changes))
    print("Planned patches:",len(planned),"mode:","APPLY" if a.apply else "DRY RUN")
    for item_id,ident,changes in planned:
        print("PATCH",ident,changes)
        if a.apply:
            modifications=[{"fieldPath":k,"action":"SET_FIELD","setFieldOptions":{"value":v}} for k,v in changes.items()]
            request(BASE+"/wix-data/v2/items/"+item_id,{"dataCollectionId":COLLECTION,"patch":{"dataItemId":item_id,"fieldModifications":modifications}},method="PATCH")
    print("Complete. No fixture rows created or deleted.")
if __name__=="__main__":
    main()
