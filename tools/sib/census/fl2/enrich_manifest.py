# Provenance: Project HERCULES | owner the owner | [id removed]
"""FL2 manifest fields (tools/fl2/BRIEF_FL2.md item 5; DECL-FL-2 item 8), added to the rows fl.py tiles wrote.
Adds per row: scroll, volume, model, model_sha256, segment_area_cm2, tifxyz_sha256 (x/y/z.tif + meta.json).
Tile pixels, file names and the existing fields are not touched. Numbers only.
Usage: enrich_manifest.py <manifest.json> <scroll> <volume> <model> <model_sha256> <measure.json> <tifxyz dir>"""
import hashlib
import json
import os
import sys


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


man_p, scroll, volume, model, model_sha, measure_p, tdir = sys.argv[1:8]
man = json.load(open(man_p))
area = json.load(open(measure_p))["area_cm2"]
tx = {f: sha256(os.path.join(tdir, f)) for f in ("x.tif", "y.tif", "z.tif", "meta.json") if os.path.exists(os.path.join(tdir, f))}
man.update({"decl": "DECL-FL-2", "volume": volume, "model": model, "model_sha256": model_sha})
for t in man["tiles"]:
    t.update({"scroll": scroll, "volume": volume, "model": model, "model_sha256": model_sha,
              "segment_area_cm2": round(float(area), 4), "tifxyz_sha256": tx})
json.dump(man, open(man_p, "w"), indent=1)
print(f"enriched {len(man['tiles'])} rows")
