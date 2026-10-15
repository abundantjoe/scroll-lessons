"""P4-W window manifest (pairs0814b e2 format + window_id). Provenance: Project HERCULES | owner the owner | [id removed]
Usage: windows_manifest.py <set_dir> <w|wpc>"""
import hashlib, json, os, sys
d, s = sys.argv[1:3]
exp = {(r, c) for r in range(7) for c in (range(9, 19) if s == "w" else range(8))}
rec = {}
for fn in sorted(os.listdir(d)):
    if fn.startswith("census_w"):
        for l in open(os.path.join(d, fn)):
            x = json.loads(l); rec[(x["r"], x["c"])] = x
el = sorted(k for k, x in rec.items() if x["eligible"])
ok = all(hashlib.sha256(open(os.path.join(d, rec[k]["file"]), "rb").read()).hexdigest() == rec[k]["png_sha256"] for k in el)
keep = ("window_id", "file", "r", "c", "png_sha256", "png_bytes", "valid_fraction", "canvas_rows", "canvas_cols", "tiles_covered", "stats")
man = {"provenance": "Project HERCULES | owner the owner | [id removed]",
       "declaration": "RULES.md DECL-P4-17 item 1 (P4-W), material L2S (DECL-P4-12-A2)", "set": s + "_l2s",
       "partial": set(rec) != exp, "window": "4 x 4 cm (16686 canvas px), stride 2 cm; r, c = top-left strip-a tile",
       "display": "L2S rule per window: linear_window_ct over mesh-valid px with max > 0, 0 elsewhere; INTER_AREA 16686 -> 1068 (26.7 px/mm); uint8 PNG",
       "source": "raw store /work/l2/raw (sha-checked against l2s/manifest.json)",
       "checks": {"n_planned": len(exp), "n_done": len(rec), "n_eligible": len(el), "png_sha256_recomputed_ok": ok,
                  "window_ids_unique": len({rec[k]["window_id"] for k in el}) == len(el)},
       "n_tiles": len(el), "tiles": [{k: rec[t][k] for k in keep} for t in el],
       "ineligible": [{"r": k[0], "c": k[1], "valid_fraction": rec[k].get("valid_fraction")} for k in sorted(rec) if not rec[k]["eligible"]]}
json.dump(man, open(os.path.join(d, "manifest.json"), "w"), indent=1)
print(s, json.dumps(man["checks"]), "partial" if man["partial"] else "COMPLETE")
