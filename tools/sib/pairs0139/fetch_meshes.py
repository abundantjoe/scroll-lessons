# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch the organizer 9.362 um and 2.399 um tifxyz (x/y/z.tif + meta.json) of every PHerc0139 segment that has a
9.362 um mesh (segment list from data/catalogue/known_text.json); sha256 into /work/p139/fetch_manifest.jsonl."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "tools/sib/pairs0139")
from fetch import get

kt = json.load(open("data/catalogue/known_text.json"))["scrolls"]["PHerc0139"]["segments"]["list"]
keys = []
for g in kt:
    if "20250728140407" not in g["meshes_on"]:
        continue
    sid = g["long_id"]; ts = sid.split("-")[0]
    for vol in ("20250728140407-9.362um", "20260102150214-2.399um"):
        for f in ("meta.json", "x.tif", "y.tif", "z.tif"):
            keys.append(f"PHerc0139/segments/{sid}/mesh/{ts}-on-{vol}.tifxyz/{f}")
with ThreadPoolExecutor(8) as ex:
    for k, (d, h) in zip(keys, ex.map(get, keys)):
        print(k, h, flush=True)
print("n_keys", len(keys))
