#!/usr/bin/env python
"""Seed generation (master prompt v4, 5.6).
Level 3 of the surface-prediction zarr (v2, uint8, blosc, axes z y x, = level-0/8) read over HTTPS or
locally, fetching ONLY the chunk planes of the chosen slices (cached under --cache). Per z-band: 5 slices;
per slice predicted voxels (>= 128) AND level-4 CT > 0 (5.8 mask criterion, CT slice z//2) are split by
centroid-distance rank into outer/middle/inner thirds and picked >= 40 level-3 voxels apart (greedy
farthest-first), ~--n-per-band per band balanced over the radii. --um is cross-checked against the CT's
metadata.json samplePixelSize and the catalogue. Output: level-0 (x, y, z) = (col*8, row*8, slice*8) in
JSON + a PNG per band (raw level-3 slices, seeds drawn, 1 cm bar = 10000/(8*um) px). Idempotent.

usage: seeds.py --scroll PHerc0306B --vol 20250521133212 --um 8.64 --auto-bands --out seeds/PHerc0306B.json
       seeds.py --pred-url <dir or https .zarr> --um 8.64 --zband 7000:8000 --n-per-band 12 --out x.json
"""
import argparse, hashlib, json, os, sys
import numpy as np
import requests
from numcodecs import Blosc
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
CATALOGUE = DATA + "/cat/metadata.min.json"
LEVEL = 3
SCALE = 2 ** LEVEL          # level-3 voxel = 8 level-0 voxels (5.6)
CT_LEVEL = 4                # 5.8: CT-mask check at level 4 (coordinates / 16)
THRESH = 128                # 5.6: predicted voxel = value >= 128
MIN_DIST = 40               # 5.6: >= 40 level-3 voxels apart
N_SLICES = 5                # 5.6: 5 slices per band
CLASSES = ("outer", "middle", "inner")
BAND_HEIGHT = 1000          # 5.6 example (PHerc0175A): bands 1000 level-0 voxels tall


# ---------------------------------------------------------------- store access (http or local)
def catalogue_entry(scroll, vol, kind, cat=CATALOGUE):
    """(URL of the catalogue data entry of type 'surface-prediction-zarr' | 'ome-zarr', pixel_size_um)."""
    v = json.load(open(cat))["samples"][scroll]["volumes"][vol]
    for d in v["data"]:
        if d.get("type") == kind:
            return BUCKET + "/" + d["origins"][0]["path"].rstrip("/"), float(v["properties"]["pixel_size_um"])
    raise KeyError(f"no {kind} for {scroll}/{vol} in catalogue")


def pred_url_from_catalogue(scroll, vol, cat=CATALOGUE):
    return catalogue_entry(scroll, vol, "surface-prediction-zarr", cat)[0]


def _cache_ns(base):
    """A cache namespace derived from the SOURCE, not just the chunk key.

    DEFECT FIXED 2026-09-19: cache files were named after the chunk key alone ("3_2_0_0", "3_.zarray"), so two runs
    over different volumes sharing one --cache directory silently served each other's chunks. Regenerating
    PHerc0358's seeds into PHerc0826's cache produced 90 seeds IDENTICAL to PHerc0826's, with PHerc0826's level-3
    shape and every per-slice n_pred, under PHerc0358's own prediction URL in the header. Caught only because two
    different scrolls cannot have identical numbers. The namespace makes the collision impossible.
    """
    return hashlib.sha1(base.rstrip("/").encode()).hexdigest()[:12]


def _get(base, key, cache=None):
    """Return the bytes of store key `key` (e.g. '3/.zarray' or '3/5/2/1') or None when absent."""
    if not base.startswith("http"):
        return open(os.path.join(base, key), "rb").read() if os.path.exists(os.path.join(base, key)) else None
    if cache:
        cp = os.path.join(cache, _cache_ns(base), key.replace("/", "_"))
        if os.path.exists(cp):
            b = open(cp, "rb").read()
            return None if b == b"" else b
    r = requests.get(base.rstrip("/") + "/" + key, timeout=120)
    data = None if r.status_code == 404 else (r.raise_for_status() or r.content)
    if cache:
        os.makedirs(os.path.dirname(cp), exist_ok=True); open(cp, "wb").write(data or b"")
    return data


def read_zarray(base, cache=None, level=LEVEL):
    b = _get(base, f"{level}/.zarray", cache)
    if b is None: raise FileNotFoundError(f"{base}/{level}/.zarray")
    m = json.loads(b)
    assert m["zarr_format"] == 2 and m["dtype"] == "|u1" and m["order"] == "C", m
    assert m.get("dimension_separator", ".") == "/", m
    assert m["compressor"] is None or m["compressor"]["id"] == "blosc", m["compressor"]
    assert not m.get("filters"), m      # only the Blosc codec is applied in read_slice
    m["_level"] = level
    return m


def read_slice(base, meta, z, cache=None):
    """Slice z of the array described by `meta` (2D uint8, axes y x), fetching only its chunk plane."""
    Z, Y, X = meta["shape"]; cz, cy, cx = meta["chunks"]; level = meta.get("_level", LEVEL)
    assert 0 <= z < Z, (z, Z)
    out = np.zeros((Y, X), np.uint8)
    codec = Blosc() if meta["compressor"] is not None else None
    fill = meta.get("fill_value") or 0
    iz, oz = divmod(z, cz)
    for iy in range((Y + cy - 1) // cy):
        for ix in range((X + cx - 1) // cx):
            raw = _get(base, f"{level}/{iz}/{iy}/{ix}", cache)
            if raw is None:
                if fill: out[iy * cy:(iy + 1) * cy, ix * cx:(ix + 1) * cx] = fill
                continue
            buf = codec.decode(raw) if codec else raw
            blk = np.frombuffer(buf, np.uint8).reshape(cz, cy, cx)[oz]
            ys, xs = slice(iy * cy, min((iy + 1) * cy, Y)), slice(ix * cx, min((ix + 1) * cx, X))
            out[ys, xs] = blk[:ys.stop - ys.start, :xs.stop - xs.start]
    return out


def check_um(ct_base, um, um_cat, cache=None):
    """Pitch (um) from <ct>.zarr/metadata.json samplePixelSize (mm), asserted == --um == catalogue."""
    m = json.loads(_get(ct_base, "metadata.json", cache))
    um_meta = float(m["scan"]["tomo"]["acquisition"]["detector"]["samplePixelSize"]) * 1000.0
    assert abs(um_meta - um) < 1e-3 and abs(um_meta - um_cat) < 1e-3, (um_meta, um, um_cat)
    return um_meta


# ---------------------------------------------------------------- selection (pure)
def band_slices(z0, z1, n=N_SLICES):
    """n level-3 slice indices spread evenly over level-0 band [z0, z1)."""
    return sorted(set(int(round(v / SCALE)) for v in np.linspace(z0, z1 - 1, n + 2)[1:-1]))


def auto_bands(z_extent0, height=BAND_HEIGHT):
    """Three bands centred at 25/50/75 % of the level-0 z extent, each `height` tall (5.6 example)."""
    z0s = [max(0, int(round(f * z_extent0)) - height // 2) for f in (0.25, 0.5, 0.75)]
    return [(z0, min(z_extent0, z0 + height)) for z0 in z0s]


def erode(mask, n):
    """Binary erosion by n pixels (square structuring element), pure numpy."""
    m = mask.copy()
    for _ in range(int(n)):
        p = np.pad(m, 1, constant_values=False)
        m = p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m


def ct_ok_mask(ct4, shape, up_factor=2, erode_px=0):
    """CT slice (level `ct_level`) -> level-3 bool mask of CT > 0 (5.8), upsampled x up_factor by repeat, cropped/padded
    (2 for the level-0 predictions of the 8-9 um scans: CT level 4 vs prediction level 3; 1 when both are at the same pitch).
    erode_px > 0 additionally removes a rim of that many level-3 pixels inside the mask boundary (the surface predictions
    carry a solid band along the scan mask where no sheet can be traced)."""
    up = np.repeat(np.repeat(ct4 > 0, up_factor, 0), up_factor, 1)
    if erode_px: up = erode(up, erode_px)
    out = np.zeros(shape, bool)
    h, w = min(shape[0], up.shape[0]), min(shape[1], up.shape[1]); out[:h, :w] = up[:h, :w]
    return out


def radius_classes(rows, cols):
    """Split voxels into outer/middle/inner thirds by rank of distance from the centroid."""
    d = np.hypot(rows - rows.mean(), cols - cols.mean())
    rank = np.argsort(np.argsort(d)); n = len(d)
    lab = np.full(n, 1, np.int8); lab[rank >= 2 * n // 3] = 0; lab[rank < n // 3] = 2   # middle/outer/inner
    return lab


def farthest_first(pts, k, taken, min_dist=MIN_DIST, rng=None):
    """Greedy farthest-first: up to k points of pts (N,2), >= min_dist from `taken` and each other."""
    if len(pts) == 0 or k <= 0: return []
    rng = rng or np.random.default_rng(0)
    if len(pts) > 20000: pts = pts[rng.choice(len(pts), 20000, replace=False)]
    pts = pts.astype(np.float64); dmin = np.full(len(pts), np.inf)
    for r, c in taken:
        dmin = np.minimum(dmin, np.hypot(pts[:, 0] - r, pts[:, 1] - c))
    chosen = []
    while len(chosen) < k:
        i = int(np.argmax(dmin))
        if dmin[i] < min_dist: break
        chosen.append((int(pts[i, 0]), int(pts[i, 1])))
        dmin = np.minimum(dmin, np.hypot(pts[:, 0] - pts[i, 0], pts[:, 1] - pts[i, 1]))
    return chosen


def select_slice(mask, n_target, rng=None, offset=0):
    """~n_target seeds on one slice balanced over the radius classes (remainder rotated by `offset`)."""
    rows, cols = np.nonzero(mask)
    if len(rows) == 0: return []
    lab = radius_classes(rows, cols)
    per = [n_target // 3 + (1 if (i - offset) % 3 < n_target % 3 else 0) for i in range(3)]
    taken, out = [], []
    for ci, name in enumerate(CLASSES):
        sel = lab == ci
        for r, c in farthest_first(np.stack([rows[sel], cols[sel]], 1), per[ci], taken, rng=rng):
            taken.append((r, c)); out.append({"row": r, "col": c, "radius": name})
    return out


def select_band(slices, n_per_band, rng=None):
    """slices: list of (slice_index, mask2d). Returns seeds in level-0 coordinates."""
    seeds, per_slice = [], []
    for k, (zi, m) in enumerate(slices):
        n_target = n_per_band // len(slices) + (1 if k < n_per_band % len(slices) else 0)
        picks = select_slice(m, n_target, rng, offset=(k * (n_target % 3 or 1)) % 3)
        per_slice.append({"slice_l3": int(zi), "n_pred": int(m.sum()), "n_seeds": len(picks)})
        for p in picks:
            seeds.append({"x": p["col"] * SCALE, "y": p["row"] * SCALE, "z": int(zi) * SCALE,
                          "radius": p["radius"], "slice_l3": int(zi), "row_l3": p["row"], "col_l3": p["col"]})
    return seeds, per_slice


# ---------------------------------------------------------------- figure
def band_png(path, slices_raw, seeds, um, title):
    import matplotlib; matplotlib.use("Agg")          # raw uint8 slices shown as stored, never thresholded
    import matplotlib.pyplot as plt
    um_px = um * SCALE; bar = int(round(10000 / um_px))
    fig, axs = plt.subplots(1, len(slices_raw), figsize=(4 * len(slices_raw), 4.4))
    col = {"outer": "tab:red", "middle": "tab:orange", "inner": "tab:cyan"}
    for ax, (zi, raw) in zip(np.atleast_1d(axs), slices_raw):
        ax.imshow(raw, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        for s in [s for s in seeds if s["slice_l3"] == zi]:
            ax.plot(s["col_l3"], s["row_l3"], "o", ms=5, mfc="none", mec=col[s["radius"]], mew=1.5)
        H, W = raw.shape
        ax.plot([W * 0.05, W * 0.05 + bar], [H * 0.95, H * 0.95], "y-", lw=3)
        ax.text(W * 0.05, H * 0.93, f"1 cm = {bar} px", color="y", fontsize=8)
        ax.set_title(f"L3 slice {zi} (z0={zi * SCALE}), {um_px:.3f} um/px", fontsize=9)
        ax.set_axis_off()
    fig.suptitle(title + "  (raw L3 prediction; seeds red outer / orange middle / cyan inner;"
                 " selection rule: threshold >= 128, CT L4 > 0)", fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return bar


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scroll"); ap.add_argument("--vol")
    ap.add_argument("--pred-url", help="prediction .zarr (https URL or local dir); default from catalogue")
    ap.add_argument("--ct-url", help="masked CT ome-zarr; default from catalogue; without a CT no 5.8 gate")
    ap.add_argument("--um", type=float, required=True, help="level-0 voxel pitch in um (checked vs metadata.json)")
    ap.add_argument("--zband", action="append", default=[], help="level-0 z0:z1, repeatable")
    ap.add_argument("--auto-bands", action="store_true", help="3 bands at 25/50/75 %% of z, 1000 tall")
    ap.add_argument("--n-per-band", type=int, default=30); ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--force", action="store_true"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--coord-scale", type=float, default=1.0,
                    help="CT level-0 voxels per prediction level-0 voxel (4 for the L2 predictions of the 2.4 um rescans; --um is then the prediction pitch)")
    ap.add_argument("--ct-level", type=int, default=CT_LEVEL, help="CT pyramid level of the 5.8 gate (4 for L0 predictions, 5 for L2 predictions)")
    ap.add_argument("--ct-up", type=int, default=2, help="upsample factor from the CT gate level to prediction level 3 (2 for L0 predictions, 1 for L2)")
    ap.add_argument("--ct-erode", type=int, default=0, help="also exclude candidates within this many level-3 px of the CT mask boundary (rim band)")
    ap.add_argument("--max-density", type=float, default=None,
                    help="exclude candidates whose level-3 neighbourhood (--density-window px square) is predicted more densely than this fraction: dense = compressed wraps where the tracer cross-cuts (RULES: seeds density gate), or the solid band along the scan mask")
    ap.add_argument("--density-window", type=int, default=15, help="side of the square window of the density gate, level-3 px (31 = 2.4 mm at 9.4 um scans)")
    a = ap.parse_args(argv)
    if os.path.exists(a.out) and not a.force:
        print("exists, skipping", a.out); return 0
    base, ct_base, um_cat, um_meta = a.pred_url, a.ct_url, None, None
    if a.scroll and a.vol:
        base = base or pred_url_from_catalogue(a.scroll, a.vol)
        ct_cat, um_cat = catalogue_entry(a.scroll, a.vol, "ome-zarr"); ct_base = ct_base or ct_cat
    meta = read_zarray(base, a.cache)
    Z3 = meta["shape"][0]; z_extent0 = Z3 * SCALE
    print("level-3 .zarray:", json.dumps({k: meta[k] for k in ("shape", "chunks", "dtype", "compressor")}))
    ct_meta, ct_cache = None, a.cache and os.path.join(a.cache, "ct")
    if ct_base:
        ct_meta = read_zarray(ct_base, ct_cache, a.ct_level)
        z_extent0 = int(round(json.loads(_get(ct_base, "0/.zarray", ct_cache))["shape"][0] / a.coord_scale))
        um_meta = check_um(ct_base, a.um / a.coord_scale, um_cat if um_cat is not None else a.um / a.coord_scale, ct_cache)
        print("CT level-4 .zarray:", json.dumps({k: ct_meta[k] for k in ("shape", "chunks", "compressor")}),
              "um metadata.json", um_meta, "catalogue", um_cat, "z extent level-0", z_extent0)
    bands = [tuple(map(int, b.split(":"))) for b in a.zband] + (auto_bands(z_extent0) if a.auto_bands else [])
    if not bands: ap.error("give --zband or --auto-bands")
    rng = np.random.default_rng(a.seed)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    result = {"scroll": a.scroll, "vol": a.vol, "pred_url": base, "ct_url": ct_base, "ct_level": a.ct_level, "ct_up": a.ct_up, "ct_erode_l3px": a.ct_erode, "max_density": a.max_density, "density_window_px": a.density_window, "coord_scale": a.coord_scale,
              "um": a.um, "um_metadata_json": um_meta, "um_catalogue": um_cat, "level": LEVEL,
              "zarray_level3": meta, "zarray_ct_level4": ct_meta, "threshold": THRESH, "min_dist_l3": MIN_DIST,
              "ct_gate": f"candidates restricted to predicted voxels with level-{a.ct_level} CT > 0 (5.8)" if ct_meta else None,
              "bar_px_l3": int(round(10000 / (a.um * SCALE))), "bands": [], "seeds": []}
    for z0, z1 in bands:
        idx = [z for z in band_slices(z0, z1) if 0 <= z < Z3]
        slices_raw, slices, ct_stats = [], [], []
        for z in idx:
            raw = read_slice(base, meta, z, a.cache); mask = raw >= THRESH; n_tot = int(mask.sum())
            if a.max_density is not None:
                from scipy.ndimage import uniform_filter
                mask &= uniform_filter(mask.astype(np.float32), a.density_window, mode="constant") <= a.max_density
            if ct_meta is not None:
                mask &= ct_ok_mask(read_slice(ct_base, ct_meta, z // a.ct_up, ct_cache), mask.shape, a.ct_up, a.ct_erode)
            slices_raw.append((z, raw)); slices.append((z, mask))
            ct_stats.append({"n_pred_total": n_tot, "n_pred_on_ct": int(mask.sum()), "ct_l4_slice": z // a.ct_up if ct_meta is not None else None})
        seeds, per_slice = select_band(slices, a.n_per_band, rng)
        for s in seeds: s["band"] = [z0, z1]
        for p, c in zip(per_slice, ct_stats): p.update(c)
        png = f"{os.path.splitext(a.out)[0]}_band_{z0}_{z1}.png"
        bar = band_png(png, slices_raw, seeds, a.um, f"{a.scroll or base} seeds band z {z0}-{z1}")
        counts = {c: sum(s["radius"] == c for s in seeds) for c in CLASSES}
        print(f"band {z0}:{z1} slices {idx} per-slice {per_slice} -> {len(seeds)} seeds {counts}")
        result["bands"].append({"z0": z0, "z1": z1, "slices": per_slice, "n_seeds": len(seeds),
                                "by_radius": counts, "png": os.path.basename(png), "bar_px": bar})
        result["seeds"] += seeds
    json.dump(result, open(a.out, "w"), indent=1)
    print("wrote", a.out, "total seeds", len(result["seeds"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
