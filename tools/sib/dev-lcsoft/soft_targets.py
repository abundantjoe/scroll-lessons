# Provenance: Project HERCULES | owner the owner | [id removed]
"""Soft-teacher targets for recipe LC384-SOFT (task dev-lcsoft; first_recipes.md recipe 2). Numbers only; pixel arrays
are never printed, displayed or written as images.

LC384-SOFT = LC384-FROZEN with one change: the target is the continuous organizer value / 255 (the pair shard's
'inkmap', the organizer 2.4 um ink map area-averaged onto the 9.362 um pixel and rounded to uint8), trained with BCE,
with no thresholds and no ignored band. Pixels that are not label-valid (not render-valid, not 2.4-um-valid) stay
unsupervised.

This script adds <cache>/soft/{inkmap.npy, sup.npy, manifest.json} next to an existing lc_cache.py cache (which it does
not modify), row-aligned with the cache's tiles.json.

Supervision mask (fail-closed). A pair shard stores label (1 ink / 0 blank / 255 ignored) and inkmap, but not the
label-valid mask lv = v24 & vo of build_pairs.py (pairs0139). lv is recovered exactly where it can be proven:
  - label in {0, 1}               -> lv is true (build_pairs sets 0/1 only inside lv);
  - label 255 on a tile whose registry valid24_frac == 1.0 (all 16384 pixels 2.4-um-valid; 1 invalid pixel would
    round to 0.9999) and whose render slice 15 (stored index 10) is > 0 (= vo) -> lv is true, so the pixel is band;
  - any other label-255 pixel     -> unsupervised (it may be outside lv). Counted as 'band_dropped_partial_tiles'.
If a shard carries an explicit boolean 'valid' array (N,128,128), sup = valid instead.
Consistency checks (any violation aborts): label 1 -> inkmap >= 150; label 0 -> inkmap <= 100; label != 255 -> vo;
every recovered band pixel has 100 <= inkmap <= 150 (the band after rounding); tile ids equal the cache's; shard
sha256 equal to the cache manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

import numpy as np

LAB_INK, LAB_BLANK = 150, 100
SURFACE_IDX = 10  # stored slices 5..25 of the -n 31 render; surface slice 15 -> index 10 (build_pairs.py Z0, ZS)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tile_sup(label, inkmap, surface, full24, valid=None):
    """-> (sup bool (128,128), counts dict). Raises ValueError on any inconsistency."""
    lab = np.asarray(label)
    im = np.asarray(inkmap)
    if valid is not None:
        sup = np.asarray(valid, bool)
        return sup, dict(explicit_valid=1, band=int((sup & (lab == 255)).sum()), band_dropped=0)
    vo = np.asarray(surface) > 0
    hard = lab != 255
    if np.any((lab == 1) & (im < LAB_INK)) or np.any((lab == 0) & (im > LAB_BLANK)):
        raise ValueError("label/inkmap threshold inconsistency")
    if np.any(hard & ~vo):
        raise ValueError("labelled pixel outside render-valid")
    cand = (lab == 255) & vo
    if full24:
        band = cand
        if np.any(band & ((im < LAB_BLANK) | (im > LAB_INK))):
            raise ValueError("recovered band pixel outside [100, 150]")
        dropped = 0
    else:
        band = np.zeros_like(cand)
        dropped = int((cand & (im >= LAB_BLANK) & (im <= LAB_INK)).sum())
    return hard | band, dict(explicit_valid=0, band=int(band.sum()), band_dropped=dropped)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="lc_cache.py output directory")
    ap.add_argument("--shards", required=True)
    ap.add_argument("--registry", required=True, help="directory of registry *.jsonl (valid24_frac per tile)")
    ap.add_argument("--out", default=None, help="default <cache>/soft")
    a = ap.parse_args(argv)
    out = a.out or os.path.join(a.cache, "soft")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    man = json.load(open(f"{a.cache}/manifest.json"))
    rows = json.load(open(f"{a.cache}/tiles.json"))
    reg = {}
    for fn in sorted(os.listdir(a.registry)):
        if fn.endswith(".jsonl"):
            for line in open(os.path.join(a.registry, fn)):
                r = json.loads(line)
                reg[r["tile_id"]] = r
    N = len(rows)
    ink = np.lib.format.open_memmap(f"{out}/inkmap.npy", mode="w+", dtype=np.uint8, shape=(N, 128, 128))
    sup = np.lib.format.open_memmap(f"{out}/sup.npy", mode="w+", dtype=np.bool_, shape=(N, 128, 128))
    cache_labels = np.load(f"{a.cache}/labels.npy", mmap_mode="r")
    tot = dict(tiles=N, tiles_full24=0, tiles_explicit_valid=0, px=N * 128 * 128, px_sup=0, px_hard=0, px_band=0,
               px_band_dropped_partial_tiles=0)
    by_shard = {}
    for i, r in enumerate(rows):
        by_shard.setdefault(r["shard"], []).append(i)
    sum_t, sum_t2 = 0.0, 0.0
    for sh, idx in sorted(by_shard.items()):
        p = os.path.join(a.shards, sh)
        got = sha(p)
        if man["shard_sha256"].get(sh) != got:
            raise ValueError(f"shard hash differs from cache manifest: {sh}")
        z = np.load(p)
        lab_all, im_all, img_all = z["label"], z["inkmap"], z["images"]
        val_all = z["valid"] if "valid" in z.files else None
        for i in idx:
            r = rows[i]
            j = r["shard_index"]
            if not np.array_equal(lab_all[j], cache_labels[i]):
                raise ValueError(f"label differs from cache row {i}")
            rr = reg.get(r["tile_id"])
            if rr is None:
                raise ValueError(f"tile {r['tile_id']} not in registry")
            full24 = float(rr["valid24_frac"]) == 1.0
            s, c = tile_sup(lab_all[j], im_all[j], img_all[j, SURFACE_IDX], full24,
                            None if val_all is None else val_all[j])
            ink[i] = im_all[j]
            sup[i] = s
            tot["tiles_full24"] += int(full24)
            tot["tiles_explicit_valid"] += c["explicit_valid"]
            tot["px_sup"] += int(s.sum())
            tot["px_hard"] += int((lab_all[j] != 255).sum())
            tot["px_band"] += c["band"]
            tot["px_band_dropped_partial_tiles"] += c["band_dropped"]
            t = im_all[j][s].astype(np.float64) / 255.0
            sum_t += float(t.sum()); sum_t2 += float((t * t).sum())
    ink.flush(); sup.flush()
    del ink, sup
    n = max(1, tot["px_sup"])
    tot.update(target_mean=sum_t / n, target_sd=float(np.sqrt(max(0.0, sum_t2 / n - (sum_t / n) ** 2))))
    m = dict(provenance="Project HERCULES | owner the owner | [id removed]", recipe="LC384-SOFT",
             target="inkmap_u8 / 255", cache_manifest_sha256=sha(f"{a.cache}/manifest.json"),
             tiles_json_sha256=sha(f"{a.cache}/tiles.json"), counts=tot, seconds=round(time.time() - t0, 1),
             files={f: sha(f"{out}/{f}") for f in ("inkmap.npy", "sup.npy")},
             code_sha256=sha(os.path.abspath(__file__)))
    json.dump(m, open(f"{out}/manifest.json", "w"), indent=1)
    print(json.dumps(dict(counts=tot, seconds=m["seconds"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
