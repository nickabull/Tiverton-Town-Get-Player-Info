#!/usr/bin/env python3
"""Archive fixed club crest files; never silently replace a previously pinned image."""
from pathlib import Path
from urllib.request import Request, urlopen
import json, subprocess, struct, sys

SOURCES = {
    "barnstapletown": "https://static.wixstatic.com/media/8aa829_4c6bb278ab2c46c49336767c95cedb89~mv2.png",
    "bideford": "https://static.wixstatic.com/media/8aa829_da6d2deb112945e1ab17de6e6f36462d~mv2.png",
    "bishopscleeve": "https://static.wixstatic.com/media/8aa829_bc015fb499ab4b4fa71b63804bc47f9b~mv2.png",
    "bristolmanorfarm": "https://static.wixstatic.com/media/8aa829_7cf5ed3ed4bc40f2b3faa6e90e66080b~mv2.png",
    "dorchestertown": "https://static.wixstatic.com/media/8aa829_2fb4a520831d4bfa8ea7e1fdf138ac51~mv2.png",
    "exmouthtown": "https://static.wixstatic.com/media/8aa829_b4cc913ef31345aabfac3ebba6b7df54~mv2.png",
    "falmouthtown": "https://static.wixstatic.com/media/8aa829_78892dbf0f4c4813b85618cb3419d7a7~mv2.png",
    "hartpury": "https://static.wixstatic.com/media/8aa829_e2d06cb8e952431f8aed9b329a02aa8c~mv2.png",
    "hungerfordtown": "https://static.wixstatic.com/media/f62a66_4fc40563b6a942d1aab1f3fdb82ef2df~mv2.png",
    "larkhallathletic": "https://static.wixstatic.com/media/8aa829_71765df901f54fbb909ebb009efa011b~mv2.png",
    "melkshamtown": "https://static.wixstatic.com/media/8aa829_e8ab9d4f1f854d039d17f7dcde8a3b4f~mv2.png",
    "paultonrovers": "https://static.wixstatic.com/media/8aa829_26e00a2cd0bc450ebd9bf1d912f5695d~mv2.png",
    "portlandunited": "https://static.wixstatic.com/media/8aa829_65009eedd74649b3b7405d2be35faff4~mv2.png",
    "shaftesbury": "https://static.wixstatic.com/media/8aa829_379295bfca974bf593c6d737ce238ad3~mv2.png",
    "slimbridge": "https://static.wixstatic.com/media/8aa829_025e16a547cc4520ad5e926a61a69e3b~mv2.png",
    "scinkberrow": "https://static.wixstatic.com/media/8aa829_a2aefe84c95b41cb924fb838ab493574~mv2.png",
    "swindonsupermarine": "https://static.wixstatic.com/media/8aa829_fc13ce065bd543e68de0c684030ace1f~mv2.png",
    "tivertontown": "https://static.wixstatic.com/media/8aa829_88bbff928f6b42f49eba4aef6c32fcb2~mv2.png",
    "westburyunited": "https://static.wixstatic.com/media/8aa829_997c5e0c7f114de7918338be91b3a2c5~mv2.png",
    "weymouth": "https://static.wixstatic.com/media/8aa829_60e64f23139143509c99a9e4bde185d3~mv2.png",
    "willandrovers": "https://static.wixstatic.com/media/8aa829_d3c15347e48c4200a3118dda1ac54a04~mv2.png",
    "worcesterraiders": "https://static.wixstatic.com/media/8aa829_54f9d56e0e9849fb996257f2521be89e~mv2.png",
}
root = Path("assets/locked-crests")
root.mkdir(parents=True, exist_ok=True)
manifest = {}
errors = []
for name, url in SOURCES.items():
    existing = next(iter(root.glob(name + ".*")), None)
    if existing:
        manifest[name] = str(existing)
        continue
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Tiverton Town crest archival)"})
        with urlopen(req, timeout=20) as response:
            body = response.read(2_000_001)
        if len(body) > 2_000_000 or len(body) < 100:
            raise ValueError("unexpected image size")
        if body.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = "png"
            w, h = struct.unpack(">II",body[16:24])
            if not 16 <= w <= 4096 or not 16 <= h <= 4096: raise ValueError("invalid dimensions")
        elif body.startswith(b"\xff\xd8\xff"):
            ext = "jpg"
        elif body.startswith(b"RIFF") and body[8:12] == b"WEBP":
            ext = "webp"
        else:
            raise ValueError("not a supported image")
        out = root / (name + "." + ext)
        out.write_bytes(body)
        manifest[name] = str(out)
        print("Archived", name, len(body), "bytes")
    except Exception as exc:
        errors.append({"club":name,"reason":str(exc)})
        print("FAILED",name,str(exc),file=sys.stderr)
(root / "manifest.json").write_text(json.dumps({"assets":manifest,"missing":errors},indent=2)+"\n")
if errors:
    print("Some crests could not be archived; live URLs remain unchanged.")
