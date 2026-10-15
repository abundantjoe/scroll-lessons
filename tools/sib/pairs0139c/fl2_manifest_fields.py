# Provenance: Project HERCULES | [id removed]
"""Adds the BRIEF_FL2 item 5 per-row fields to a template tiles manifest (rows only gain keys; nothing is removed):
scroll, volume, segment, model, model_sha256, direction, r, c, valid_fraction, ink_score_ge128, px_per_mm,
segment_area_cm2. Usage: fl2_manifest_fields.py MANIFEST MEASURE_JSON VOLUME [extra_key=value ...]"""
import json, sys
man, me, vol = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
extra = dict(a.split("=", 1) for a in sys.argv[4:])
for t in man["tiles"]:
    t.update(scroll="PHerc0139", volume=vol, model="ink_9um hybrid_3d2d-seed42 step-075000 (HF scrollprize/ink_9um @7109667e)",
             model_sha256="e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab",
             segment_area_cm2=round(me["area_cm2"], 4), **extra)
man["segment_tifxyz_x_sha256"] = me.get("x_tif_sha256")
json.dump(man, open(sys.argv[1], "w"), indent=1)
print(f"manifest fields added: {len(man['tiles'])} rows")
