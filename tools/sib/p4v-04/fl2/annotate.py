# Provenance: Project HERCULES | [id removed]
# DECL-FL-2 brief item 5: add the per-row fields scroll, volume, segment, model, model_sha256, segment_area_cm2 to a
# fl.py tiles manifest. Bookkeeping only (reads JSON, never an image).
# usage: annotate.py manifest.json SCROLL VOLUME SEGMENT MODEL MODEL_SHA256 measure.json
import json, sys

man_p, scroll, volume, seg, model, msha, meas_p = sys.argv[1:8]
man = json.load(open(man_p))
area = json.load(open(meas_p))["area_cm2"]
man.update({"decl": "DECL-FL-2", "volume": volume, "model": model, "model_sha256": msha})
for t in man["tiles"]:
    assert t["segment"] == seg, (t["segment"], seg)
    t.update({"scroll": scroll, "volume": volume, "model": model, "model_sha256": msha,
              "segment_area_cm2": round(float(area), 4)})
json.dump(man, open(man_p, "w"), indent=1)
print(f"annotate {seg} {model}: {len(man['tiles'])} rows")
