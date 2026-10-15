# Provenance: Project HERCULES | owner the owner | [id removed]
"""Example control manifest built by code from clean PHerc0139 only (plan section 6.8.7).
Geometry only: no ink map, CT or image is opened. Numbers the orchestrator must supply
after D3 (sigma_mm, REF ceilings, source sha256 after its own fetch) are left null, so the
builder refuses this file until they are filled in.

Window choice: 2 x 2 cm squares (2136 px at 9.362 um) on the canvases of the clean bank
segments w024 and w053, stride 1068 px, >= 95 % mesh-valid, and no densified (4 vox)
vertex within 2 + 2*sqrt(2) vox of any base-training trace (a conservative superset of
the corrected 2-vox surface rule) inside the window plus a 64 px halo; the SEAL-J-D1
blank windows (+ halo) are excluded; windows do not overlap; order (segment, y, x).

    python tools/sib/tribunal/make_example_manifest.py MESH_ROOT meshes_fetched.json OUT.json [DEV_REGISTRY.json]
With DEV_REGISTRY, windows are also canvas-disjoint (+64 px halo) from every used, DEV and D1 0139 window
(devloop registry used_windows_0139, its DEV windows and blanks, logs/d1/d1_build_prep.json).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from hercules.geometry.tifxyz import densify, read_tifxyz, sample_grid, valid_mask
from hercules.tribunal import controls as K
from hercules.tribunal.manifest import validate_manifest

WIN, STRIDE, HALO = 2136, 1068, 64
NEAR = 2.0 + 2.0 * math.sqrt(2.0)
BASE = ["w028", "w029", "w030", "w035", "w039", "w040", "w041", "w043", "w044", "w045", "w046"]  # w028: devloop R3 (ink_9um label list)
BLANKS = [("w053", 256, 1536), ("w053", 256, 7168)]
PER_SEG = 3
VOL_URL = "s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr"


def _find_long_id(obj, sid):
    """Catalogue record whose long_id is ``sid`` (known_text.json nests them per scroll)."""
    if isinstance(obj, dict):
        if obj.get("long_id") == sid:
            return obj
        obj = list(obj.values())
    if isinstance(obj, list):
        for x in obj:
            r = _find_long_id(x, sid)
            if r is not None:
                return r
    return None


def main():
    fetched = json.loads(Path(sys.argv[2]).read_text())
    out = Path(sys.argv[3])
    used = {}
    if len(sys.argv) > 4:
        reg = json.loads(Path(sys.argv[4]).read_text())
        sc = reg["scrolls"]["PHerc0139"]
        for w in reg["used_windows_0139"]:
            used.setdefault(w["segment"], []).append((w["y0"], w["x0"], w["size"]))
        for w in sc["windows"] + sc["blanks"]:
            used.setdefault(w["segment"], []).append((w["y0"], w["x0"], max(w["h"], w["w"])))
        for w in json.loads(Path("logs/d1/d1_build_prep.json").read_text())["windows"].values():
            if w["scroll"] == "PHerc0139":
                ow = w["organizer_window"]
                used.setdefault(w["segment_short"], []).append((ow["y0"], ow["x0"], max(ow["h"], ow["w"])))
    ids = {k.split("/")[1]: v["mesh"] for k, v in fetched["segments"].items() if k.startswith("PHerc0139/") and "mesh" in v}
    find = lambda t: sorted(s for s in ids if f"-{t}_" in s)  # noqa: E731
    base_pts = np.concatenate([(lambda d: d[valid_mask(d)])(densify(read_tifxyz(ids[s]).points.astype(np.float64), 5))
                               for t in BASE for s in find(t)])
    tree = cKDTree(base_pts)
    kt = json.loads(Path("data/catalogue/known_text.json").read_text())
    chosen = []
    for tag in ("w024", "w053"):
        sid = find(tag)[0]
        p = read_tifxyz(ids[sid]).points.astype(np.float64)
        dn = densify(p, 5)
        v = valid_mask(dn)
        d, _ = tree.query(dn[v], k=1, distance_upper_bound=NEAR + 1e-9, workers=3)
        rr, cc = np.nonzero(v)
        bad = np.isfinite(d)
        bad_px = np.stack([rr[bad] * 4.0 - 0.5, cc[bad] * 4.0 - 0.5], 1)  # dense index k -> canvas 4k - 0.5
        btree = cKDTree(bad_px) if len(bad_px) else None
        Hc, Wc = p.shape[0] * 20, p.shape[1] * 20
        taken = []
        for y0 in range(0, Hc - WIN + 1, STRIDE):
            for x0 in range(0, Wc - WIN + 1, STRIDE):
                if len(taken) >= PER_SEG:
                    break
                if any(abs(y0 - a) < WIN and abs(x0 - b) < WIN for a, b in taken):
                    continue
                if any(t == tag and abs(y0 - by) < WIN + HALO and abs(x0 - bx) < WIN + HALO for t, by, bx in BLANKS):
                    continue
                if any(abs((y0 + WIN / 2) - (a + z / 2)) < (WIN + z) / 2 + HALO and
                       abs((x0 + WIN / 2) - (b + z / 2)) < (WIN + z) / 2 + HALO for a, b, z in used.get(tag, [])):
                    continue
                rows = (np.arange(y0, y0 + WIN, 8) + 0.5) / 20.0
                cols = (np.arange(x0, x0 + WIN, 8) + 0.5) / 20.0
                R, C = np.meshgrid(rows, cols, indexing="ij")
                if valid_mask(sample_grid(p, R, C)).mean() < 0.95:
                    continue
                if btree is not None:
                    cy, cx = y0 + WIN / 2.0, x0 + WIN / 2.0
                    near = btree.query_ball_point([cy, cx], r=(WIN / 2.0 + HALO) * math.sqrt(2.0))
                    q = bad_px[near] if near else np.zeros((0, 2))
                    inside = ((q[:, 0] >= y0 - HALO) & (q[:, 0] < y0 + WIN + HALO) &
                              (q[:, 1] >= x0 - HALO) & (q[:, 1] < x0 + WIN + HALO))
                    if inside.any():
                        continue
                taken.append((y0, x0))
        seg_rec = _find_long_id(kt, sid)
        refkey = next((x["path"] for x in (seg_rec or {}).get("ink_maps", [])
                       if "-2.399um-" in x.get("path", "")), None)
        for y0, x0 in taken:
            chosen.append({"segment": sid, "tag": tag, "window": {"y0": y0, "x0": x0, "h": WIN, "w": WIN},
                           "ref_map_key": refkey})
    canaries = [{"canary_id": f"pc{i + 1}", "tile": {"scroll": "PHerc0139", "segment": c["segment"], "window": c["window"]},
                 "ref_map": {"source": (f"s3://vesuvius-challenge-open-data/{c['ref_map_key']}" if c["ref_map_key"] else
                                        f"official 2.399 um reference map of {c['segment']}")
                             + " -> 9.362 um levelled canvas (labelmap formula), window crop", "sha256": None},
                 "sigma_mm": None, "ref_ceiling": {"recall": None, "rows_found": None}, "seal_sha256": None}
                for i, c in enumerate(chosen[:-1])]
    last = chosen[-1]
    tile = {"scroll": "PHerc0139", "segment": last["segment"], "window": last["window"]}
    m = {
        "manifest_version": 1, "batch_id": "EXAMPLE",
        "status": "EXAMPLE: sigma_mm, ref_ceiling, seal_sha256 and every sha256 to be supplied by the orchestrator after D3; "
                  "remove any window that lies in a sealed or used set (READ-CAL, PROBE, D1/D3) - those lists are not in this container",
        "voxel": {"metadata_source": VOL_URL + "/metadata.json", "voxel_um": None},
        "display": {"window": "raw", "display_scale": 0.5},
        "positive_canaries": canaries,
        "baits": [
            {"bait_id": "bait_wrong_order", "kind": "wrong_order", "tile": tile,
             "map": {"source": "base ink_9um C2-NT map, NON-text (reverse) direction, of the tile", "sha256": None}},
            {"bait_id": "bait_null_arm", "kind": "null_arm", "tile": tile,
             "map": {"source": "NULL-arm checkpoint map, text direction, of the tile", "sha256": None}},
            {"bait_id": "bait_blank", "kind": "blank", "tile": canaries[0]["tile"], "map": None,
             "blank_mode": "phase_scramble", "derive_from": "pc1"},
        ],
        "mirror_canaries": {"glyphs": "".join(K.MIRROR_GLYPHS), "letter_height_mm": 3.0, "sigma_mm": None,
                            "canvas_hw": [WIN, WIN], "font_sha256": K.font_sha256()},
        "selection": {"rule": __doc__.split("Window choice:")[1].split("python tools")[0].strip(),
                      "base_training_traces": [s for t in BASE for s in find(t)], "near_vox": NEAR,
                      "used_dev_d1_windows_excluded": sum(len(v) for v in used.values()),
                      "n_windows": len(chosen)},
    }
    m["validation_structure_errors"] = validate_manifest(m, for_build=False)
    m["validation_build_errors"] = validate_manifest(m, for_build=True)
    out.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
    print(len(chosen), "windows;", "structure errors:", m["validation_structure_errors"])


if __name__ == "__main__":
    main()
