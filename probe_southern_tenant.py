#!/usr/bin/env python3
"""Inspect publicly-served league HTML for the documented tenant identifier.
Read-only; don't guess tenant IDs or probe private endpoints.
"""
import re, json
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from urllib.error import HTTPError,URLError

sites=["https://www.southern-football-league.co.uk/match/6a5a1cc3ce9ef452b61f4489","https://slc-www.southern-football-league.co.uk/match/6a5a1cc3ce9ef452b61f4489"]
res=[]
for url in sites:
 row={"url":url,"status":None,"header_matches":[],"scripts":[],"public_config_matches":[]}
 try:
  req=Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
  with urlopen(req,timeout=18) as f:
   row["status"]=f.status
   data=f.read(1200000).decode("utf-8","replace")
   for k,v in f.headers.items():
    if "tenant" in k.lower(): row["header_matches"].append([k,v[:100]])
  for m in re.finditer(r'.{0,80}(?:X-TENANT-ID|tenantId|tenant_id|tenant-id|tenantIdentifier|tenant:\\").{0,170}',data,re.I):
   row["public_config_matches"].append(m.group(0)[:240])
  row["scripts"]=[urljoin(url,a) for a in re.findall(r'<script[^>]+src=["\\x27]([^"\\x27]+)',data,re.I)][:12]
  row["page_bytes"]=len(data)
 except (HTTPError,URLError,TimeoutError) as e:row["error"]=str(e)[:150]
 res.append(row)
 print(json.dumps(row,ensure_ascii=False),flush=True)
with open("southern-league-public-tenant-inspection.json","w") as f:json.dump(res,f,indent=2)
