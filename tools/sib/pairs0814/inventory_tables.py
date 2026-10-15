# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task pairs0814: per-scroll segment inventory tables from segment_inventory.json (and the root index for the
registration transforms). Writes logs/sib/pairs0814/inventory_<scroll>.json for each scroll; the PHerc0500P2 table is
the held-out-fold inventory the task asks for when a scroll matches JULY. No data are fetched here."""
import json
import os
import re

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
LOGD = f"{REPO}/logs/sib/pairs0814"
ROOT_INDEX = "/work/sib/meta/root_metadata.json"
PROV = "Project HERCULES | owner the owner | [id removed]"
RES = re.compile(r"(\d+\.\d+)um")


def res_of(s):
    m = RES.search(s)
    return m.group(1) if m else None


def main():
    inv = json.load(open(f"{LOGD}/segment_inventory.json"))["inventory"]
    prot = json.load(open(f"{LOGD}/protocol_check.json"))["protocol"]
    idx = json.load(open(ROOT_INDEX))["samples"] if os.path.exists(ROOT_INDEX) else {}
    for sc, d in inv.items():
        segs = []
        for name, r in sorted(d["segments"].items()):
            ink = r["ink_maps"]
            segs.append(dict(
                segment=name, indexed=r["indexed"],
                original_volume_id=(r.get("index") or {}).get("original_volume_id"),
                meshes_tifxyz={res_of(m) or m: m for m in r["meshes_tifxyz"]},
                n_obj=len(r["meshes_obj"]),
                surface_volumes=sorted({res_of(s) + ("-L1" if "-L1" in s else "") for s in r["surface_volumes"] if res_of(s)}),
                ink_maps=[dict(file=f, bytes=n, resolution_um=res_of(f)) for f, n in ink],
                ink_label_sets=r["ink_labels"],
                top_level_subdirs=sorted(r["subdirs"]),
            ))
        tf = []
        vt = (((idx.get(sc) or {}).get("sample") or {}).get("properties") or {}).get("volume_transforms") or []
        for v in vt:
            for t in v["transforms"]:
                tf.append(dict(from_volume=v["from_volume_id"], to_volume=t["to_volume_id"],
                               derivation=t.get("derivation_path")))
        counts = dict(
            segments=len(segs),
            with_9p362_mesh=sum(1 for s in segs if "9.362" in s["meshes_tifxyz"]),
            with_9p362_sv=sum(1 for s in segs if "9.362" in s["surface_volumes"]),
            with_highres_mesh=sum(1 for s in segs if any(float(k) < 5 for k in s["meshes_tifxyz"] if k and k[0].isdigit())),
            with_highres_sv=sum(1 for s in segs if any(float(x.split("-")[0]) < 5 for x in s["surface_volumes"])),
            with_ink_map=sum(1 for s in segs if s["ink_maps"]),
            ink_maps_by_resolution={k: sum(1 for s in segs for m in s["ink_maps"] if m["resolution_um"] == k)
                                    for k in sorted({m["resolution_um"] for s in segs for m in s["ink_maps"]}, key=str)},
            with_ink_labels=sum(1 for s in segs if s["ink_label_sets"]),
        )
        out = dict(provenance=PROV, scroll=sc, protocol_verdict=prot[sc]["verdict"],
                   JULY_match_volumes=prot[sc]["JULY_match_volumes"], MAY_match_volumes=prot[sc]["MAY_match_volumes"],
                   volumes=d["volumes"], index_volume_transforms=tf, counts=counts,
                   unindexed_or_raw=[s["segment"] for s in segs if not s["indexed"]], segments=segs)
        json.dump(out, open(f"{LOGD}/inventory_{sc}.json", "w"), indent=1)
        print(sc, prot[sc]["verdict"], json.dumps(counts), "transforms:", [(t["from_volume"], t["to_volume"]) for t in tf])


if __name__ == "__main__":
    main()
