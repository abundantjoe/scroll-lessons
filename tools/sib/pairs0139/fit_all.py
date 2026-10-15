# Provenance: Project HERCULES | owner the owner | [id removed]
"""Run meshfit.fit on every PHerc0139 segment with a 9.362 um mesh -> /work/p139/affines.json (+ sha256 of inputs)."""
import json, hashlib, time
from meshfit import fit, TJSON

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

kt = json.load(open("data/catalogue/known_text.json"))["scrolls"]["PHerc0139"]["segments"]["list"]
out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           transform_json=TJSON, transform_json_sha256=sha(TJSON), segments={})
for g in kt:
    if "20250728140407" not in g["meshes_on"]:
        continue
    s = g["long_id"]; ts = s.split("-")[0]
    t = time.time()
    r = fit(f"/work/p139/s3/PHerc0139/segments/{s}", ts)
    r["seconds"] = round(time.time() - t, 1)
    out["segments"][s] = r
    print(s, r["scale_rows"], r["scale_cols"], r["fit_res_px9"]["max"], r["offsurface_res_vox"]["p95"],
          r["frac_used"], r["plain_scaling_dev_um"]["corner_max"], flush=True)
json.dump(out, open("/work/p139/affines.json", "w"), indent=1)
